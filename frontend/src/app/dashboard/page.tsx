"use client";

import { useState, useCallback, useMemo, Fragment } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, Monitor, Server, Database, Cloud, History, LogOut, Layers, RefreshCw, Palette, TestTube, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import FloatingAIAgent from "@/components/FloatingAIAgent";
import type { Module, SubTask } from "@/types/dashboard";
import { ProposalData, ResourceRow, TechRec, calcTotal, fmtNum, getPhaseRatios } from "@/lib/utils";
import { EstimateInputSection } from "../../components/EstimateInputSection";
import { EstimatesResultsSection } from "../../components/EstimatesResultsSection";
import { ProposalsSection } from "../../components/ProposalsSection";

const API_BASE =
  (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_BASE) ||
  "http://localhost:8000";

function transformEstimateResponse(data: any) {
  const estimation = data.estimation || {};
  const features: any[] = estimation.features || [];
  const techStackData = data.tech_stack || {};
  const planning = data.planning || {};
  const domainDetection = data.domain_detection || {};
  const proposalRaw = data.proposal || {};

  const ratios = getPhaseRatios(planning.phase_split) ?? { frontend: 0.4, backend: 0.35, integration: 0, testing: 0.15 };

  const tasks: SubTask[] = features.map((f: any, i: number) => {
    const hours = Number(f.estimated_hours) || 0;
    const fe = Math.round(hours * ratios.frontend);
    const be = Math.round(hours * ratios.backend);
    const test = Math.round(hours * ratios.testing);
    const integ = Math.max(0, hours - fe - be - test);
    return {
      id: String(i + 1), name: (f.name || f.description || "").trim() || `Feature ${i + 1}`,
      frontend: fe, backend: be, integration: integ, testing: test, total: hours, complexity: f.complexity,
    };
  });

  const domainStr = (domainDetection.detected_domain ?? "").toString().replace(/_/g, " ").trim();
  const moduleName = domainStr ? domainStr.charAt(0).toUpperCase() + domainStr.slice(1) : "Project";
  const modules: Module[] = [{ id: "1", name: moduleName, expanded: true, tasks }];

  const justification = (techStackData.justification ?? "").toString();
  const techStack: TechRec[] = [
    ...(Array.isArray(techStackData.frontend) && techStackData.frontend.length ? [{ category: "Frontend", tech: techStackData.frontend.join(", "), reason: justification, icon: Monitor }] : []),
    ...(Array.isArray(techStackData.backend) && techStackData.backend.length ? [{ category: "Backend", tech: techStackData.backend.join(", "), reason: justification, icon: Server }] : []),
    ...(Array.isArray(techStackData.database) && techStackData.database.length ? [{ category: "Database", tech: techStackData.database.join(", "), reason: justification, icon: Database }] : []),
    ...(Array.isArray(techStackData.infrastructure) && techStackData.infrastructure.length ? [{ category: "Infrastructure", tech: techStackData.infrastructure.join(", "), reason: justification, icon: Cloud }] : []),
    ...(Array.isArray(techStackData.third_party_services) && techStackData.third_party_services.length ? [{ category: "Services", tech: techStackData.third_party_services.join(", "), reason: justification, icon: Zap }] : []),
  ];

  const teamRec: Record<string, unknown> = planning.team_recommendation || proposalRaw.team_composition || {};
  const resources: ResourceRow[] = Object.entries(teamRec).map(([role, count]) => {
    const n = Number(count) || 0;
    return { role, senior: 0, mid: n, junior: 0, total: n };
  });

  const totalHours = Number(estimation.total_hours) || 0;
  const timelineWeeks = proposalRaw.timeline_weeks ?? planning.timeline_weeks;
  const summary = {
    domain: domainStr, totalHours,
    timeline: timelineWeeks != null ? `${timelineWeeks} weeks` : "",
    confidence: Math.round(Number(estimation.confidence_score || domainDetection.confidence || 0) * 100),
  };

  const proposal: ProposalData = {
    executiveSummary: proposalRaw.executive_summary || "", scopeOfWork: proposalRaw.scope_of_work || "",
    deliverables: Array.isArray(proposalRaw.deliverables) ? proposalRaw.deliverables : [],
    risks: Array.isArray(proposalRaw.risks) ? proposalRaw.risks : [],
    assumptions: Array.isArray(estimation.assumptions) ? estimation.assumptions : [],
    minHours: Number(estimation.min_hours) || 0, maxHours: Number(estimation.max_hours) || 0,
  };

  return { modules, techStack, resources, summary, proposal };
}

async function fetchEstimate(payload: { project_description: string; platforms?: string[]; timeline?: string; }): Promise<any> {
  const body: Record<string, unknown> = {
    project_description: payload.project_description.trim(),
    timeline_constraint: payload.timeline || undefined,
    additional_context: payload.platforms?.length ? `Platforms: ${payload.platforms.join(", ")}` : undefined,
  };
  const response = await fetch(`${API_BASE}/estimate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!response.ok) { const err = await response.text().catch(() => ""); throw new Error(`API ${response.status}: ${err || response.statusText}`); }
  return response.json();
}

export default function DashboardPage() {
  const [projectDesc, setProjectDesc] = useState("");
  const [platforms, setPlatforms] = useState<string[]>([]);
  const [timeline, setTimeline] = useState("");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [modules, setModules] = useState<Module[]>([]);
  const [techStack, setTechStack] = useState<TechRec[]>([]);
  const [resources, setResources] = useState<ResourceRow[]>([]);
  const [summaryData, setSummaryData] = useState({ domain: "", totalHours: 0, timeline: "", confidence: 0 });
  const [proposalData, setProposalData] = useState<ProposalData | null>(null);
  const [rawApiResponse, setRawApiResponse] = useState<any>(null);
  const [taskExpanded, setTaskExpanded] = useState<Record<string, boolean>>({});
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});
  const { toast } = useToast();

  const togglePlatform = useCallback((value: string) => {
    setPlatforms((prev) => prev.includes(value) ? prev.filter((p) => p !== value) : [...prev, value]);
  }, []);

  const toggleModule = useCallback((id: string) => setModules((p) => p.map((m) => (m.id === id ? { ...m, expanded: !m.expanded } : m))), []);
  const toggleTask = useCallback((id: string) => setTaskExpanded((p) => ({ ...p, [id]: !p[id] })), []);
  const expandAll = useCallback(() => setModules((p) => p.map((m) => ({ ...m, expanded: true }))), []);
  const collapseAll = useCallback(() => setModules((p) => p.map((m) => ({ ...m, expanded: false }))), []);
  const toggleSection = (key: string) => setExpandedSections(p => ({ ...p, [key]: !p[key] }));

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null; setUploadedFile(file);
    if (file) toast({ title: `File selected: ${file.name}` });
  }, [toast]);

  const handleFileDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault(); const file = e.dataTransfer.files?.[0] || null; setUploadedFile(file);
    if (file) toast({ title: `File selected: ${file.name}` });
  }, [toast]);

  const handleGenerate = useCallback(async () => {
    const desc = projectDesc.trim();
    if (!desc && !uploadedFile) { toast({ title: "Enter a description or upload a file", variant: "destructive" }); return; }
    if (desc.length > 0 && desc.length < 10) { toast({ title: "Description must be at least 10 characters", variant: "destructive" }); return; }
    setLoading(true); setError(null);
    try {
      const raw = await fetchEstimate({ project_description: desc, platforms: platforms.length ? platforms : undefined, timeline: timeline || undefined });
      setRawApiResponse(raw);
      const { modules: mods, techStack: ts, resources: res, summary, proposal } = transformEstimateResponse(raw);
      setModules(mods); setTechStack(ts); setResources(res); setSummaryData(summary); setProposalData(proposal);
      setShowResults(true); toast({ title: "Estimation ready!" });
    } catch (err: any) {
      const msg = err?.message || "";
      const isNet = msg === "Failed to fetch" || msg.includes("NetworkError") || msg.includes("Load failed");
      const userMsg = isNet ? `Cannot reach API at ${API_BASE}. Make sure the backend is running.` : msg || "Estimation failed.";
      setError(userMsg); toast({ title: "Estimation failed", description: userMsg, variant: "destructive" });
    } finally { setLoading(false); }
  }, [projectDesc, platforms, timeline, uploadedFile, toast]);

  const handleNewEstimation = useCallback(() => {
    setShowResults(false); setModules([]); setTechStack([]); setResources([]);
    setSummaryData({ domain: "", totalHours: 0, timeline: "", confidence: 0 });
    setProposalData(null); setRawApiResponse(null); setError(null);
    setProjectDesc(""); setPlatforms([]); setTimeline("");
    setUploadedFile(null); setTaskExpanded({}); setSearchQuery(""); setExpandedSections({});
  }, []);

  const updateTaskField = useCallback((moduleId: string, taskId: string, field: "frontend" | "backend" | "integration" | "testing", value: number, childId?: string) => {
    setModules((prev) => prev.map((m) => {
      if (m.id !== moduleId) return m;
      return {
        ...m, tasks: m.tasks.map((t) => {
          if (childId && t.id === taskId) {
            const kids = t.children?.map((c) => { if (c.id !== childId) return c; const u = { ...c, [field]: value }; u.total = calcTotal(u); return u; });
            const p = { ...t, children: kids };
            if (kids?.length) { p.frontend = kids.reduce((a, c) => a + c.frontend, 0); p.backend = kids.reduce((a, c) => a + c.backend, 0); p.integration = kids.reduce((a, c) => a + (c.integration ?? 0), 0); p.testing = kids.reduce((a, c) => a + c.testing, 0); p.total = calcTotal(p); }
            return p;
          }
          if (t.id !== taskId) return t;
          const u = { ...t, [field]: value }; u.total = calcTotal(u); return u;
        })
      };
    }));
  }, []);

  const updateTaskName = useCallback((moduleId: string, taskId: string, name: string, childId?: string) => {
    setModules((prev) => prev.map((m) => {
      if (m.id !== moduleId) return m;
      return {
        ...m, tasks: m.tasks.map((t) => {
          if (childId && t.id === taskId) return { ...t, children: t.children?.map((c) => (c.id === childId ? { ...c, name } : c)) };
          if (t.id === taskId) return { ...t, name }; return t;
        })
      };
    }));
  }, []);

  const deleteTask = useCallback((moduleId: string, taskId: string, childId?: string) => {
    setModules((prev) => prev.map((m) => {
      if (m.id !== moduleId) return m;
      if (childId) {
        return {
          ...m, tasks: m.tasks.map((t) => {
            if (t.id !== taskId) return t;
            const kids = t.children?.filter((c) => c.id !== childId); const u = { ...t, children: kids };
            if (kids?.length) { u.frontend = kids.reduce((a, c) => a + c.frontend, 0); u.backend = kids.reduce((a, c) => a + c.backend, 0); u.integration = kids.reduce((a, c) => a + (c.integration ?? 0), 0); u.testing = kids.reduce((a, c) => a + c.testing, 0); u.total = calcTotal(u); }
            return u;
          })
        };
      }
      return { ...m, tasks: m.tasks.filter((t) => t.id !== taskId) };
    }));
    toast({ title: "Deleted" });
  }, [toast]);

  const addSubFeature = useCallback((moduleId: string, taskId: string) => {
    setModules((prev) => prev.map((m) => {
      if (m.id !== moduleId) return m;
      return {
        ...m, tasks: m.tasks.map((t) => {
          if (t.id !== taskId) return t;
          const child: SubTask = { id: `${t.id}.${(t.children?.length || 0) + 1}`, name: "New sub-feature", frontend: 0, backend: 0, integration: 0, testing: 0, total: 0 };
          return { ...t, children: [...(t.children || []), child] };
        })
      };
    }));
    setTaskExpanded((p) => ({ ...p, [taskId]: true })); toast({ title: "Sub-feature added" });
  }, [toast]);

  const addTask = useCallback((moduleId: string) => {
    setModules((prev) => prev.map((m) => {
      if (m.id !== moduleId) return m;
      const task: SubTask = { id: `${m.id}.${m.tasks.length + 1}`, name: "New feature", frontend: 0, backend: 0, integration: 0, testing: 0, total: 0 };
      return { ...m, tasks: [...m.tasks, task], expanded: true };
    }));
    toast({ title: "Feature added" });
  }, [toast]);

  const filteredModules = useMemo(() => {
    if (!searchQuery.trim()) return modules;
    const q = searchQuery.toLowerCase();
    return modules.map((m) => ({ ...m, tasks: m.tasks.filter((t) => t.name.toLowerCase().includes(q) || m.name.toLowerCase().includes(q)) })).filter((m) => m.name.toLowerCase().includes(q) || m.tasks.length > 0);
  }, [modules, searchQuery]);

  const totalsByColumn = useMemo(() =>
    modules.reduce((acc, m) => { m.tasks.forEach((t) => { acc.frontend += t.frontend; acc.backend += t.backend; acc.integration += (t.integration ?? 0); acc.testing += t.testing; acc.total += t.total; }); return acc; }, { frontend: 0, backend: 0, integration: 0, testing: 0, total: 0 }),
    [modules]);

  const featureCount = useMemo(() => modules.reduce((a, m) => a + m.tasks.length, 0), [modules]);

  const statCards = useMemo(() => [
    { label: "Total Hours", value: fmtNum(totalsByColumn.total), meta: `${modules.length} modules · ${featureCount} features`, color: "text-foreground", iconColor: "text-primary", bg: "stat-blue", icon: Layers },
    { label: "Frontend", value: fmtNum(totalsByColumn.frontend), color: "text-blue-400", iconColor: "text-blue-400", bg: "stat-blue", icon: Palette },
    { label: "Backend", value: fmtNum(totalsByColumn.backend), color: "text-violet-400", iconColor: "text-violet-400", bg: "stat-purple", icon: Server },
    { label: "Testing / QA", value: fmtNum(totalsByColumn.testing), meta: "Quality assurance", color: "text-emerald-400", iconColor: "text-emerald-400", bg: "stat-green", icon: TestTube },
  ], [totalsByColumn, modules.length, featureCount]);

  /* ═══════════════════════════════════════════════════════════════════════
     RENDER
     ═══════════════════════════════════════════════════════════════════════ */
  return (
    <div className="min-h-screen relative bg-background">
      {/* ── Ambient background ──────────────────────────────────────── */}
      <div className="fixed inset-0 pointer-events-none z-0 dot-grid opacity-30" />
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute top-[-12%] right-[-8%] w-[550px] h-[550px] rounded-full opacity-60"
          style={{ background: "radial-gradient(circle, hsl(230 94% 68% / 0.1), transparent 55%)", filter: "blur(90px)", animation: "aurora-float 20s ease-in-out infinite alternate" }} />
        <div className="absolute bottom-[5%] left-[-6%] w-[450px] h-[450px] rounded-full opacity-50"
          style={{ background: "radial-gradient(circle, hsl(270 88% 68% / 0.08), transparent 55%)", filter: "blur(90px)", animation: "aurora-float 16s ease-in-out infinite alternate-reverse" }} />
      </div>

      {/* ── Navbar ──────────────────────────────────────────────────── */}
      <nav className="sticky top-0 z-40 border-b border-border/30" style={{ background: "hsl(var(--card) / 0.6)", backdropFilter: "blur(20px) saturate(1.5)" }}>
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/20 to-transparent pointer-events-none" />
        <div className="container mx-auto flex items-center justify-between h-14 px-4">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="w-9 h-9 rounded-xl gradient-bg flex items-center justify-center shrink-0 shadow-lg shadow-primary/25 group-hover:shadow-primary/40 group-hover:scale-105 transition-all duration-300">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-bold hidden sm:block tracking-tight" style={{ fontFamily: "'Sora', system-ui" }}>Neural Architects</span>
            </Link>
            {showResults && summaryData.domain && (
              <motion.div initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} className="hidden md:flex items-center gap-1.5 ml-3 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/15">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-[11px] font-semibold text-emerald-400 capitalize">{summaryData.domain}</span>
              </motion.div>
            )}
          </div>
          <div className="flex items-center gap-2">
            {showResults && (
              <Button variant="outline" size="sm" onClick={handleNewEstimation} className="rounded-xl border-border/40 hover:border-primary/30 hover:bg-primary/5 text-xs font-medium">
                <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> New
              </Button>
            )}
            <Link href="/history"><Button variant="outline" size="sm" className="rounded-xl border-border/40 hover:border-primary/30 hover:bg-primary/5 text-xs font-medium"><History className="w-3.5 h-3.5 mr-1.5" /><span className="hidden sm:inline">History</span></Button></Link>
            <Link href="/"><Button variant="ghost" size="sm" className="rounded-xl text-muted-foreground hover:text-foreground"><LogOut className="w-4 h-4" /></Button></Link>
          </div>
        </div>
      </nav>

      {/* ── Main ───────────────────────────────────────────────────── */}
      <div className="container mx-auto px-4 py-8 relative z-10">
        <Tabs defaultValue="estimates" className="space-y-6">
          <div className="flex items-center justify-between">
            <TabsList>
              <TabsTrigger value="estimates">Estimates</TabsTrigger>
              <TabsTrigger value="proposals">Proposals</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="estimates">
            <AnimatePresence mode="wait">
              {!showResults ? (
                <EstimateInputSection
                  projectDesc={projectDesc}
                  platforms={platforms}
                  timeline={timeline}
                  uploadedFile={uploadedFile}
                  loading={loading}
                  error={error}
                  onChangeProjectDesc={setProjectDesc}
                  onTogglePlatform={togglePlatform}
                  onChangeTimeline={setTimeline}
                  onFileChange={handleFileChange}
                  onFileDrop={handleFileDrop}
                  onGenerate={handleGenerate}
                />
              ) : (
                <EstimatesResultsSection
                  statCards={statCards}
                  summaryData={summaryData}
                  proposalData={proposalData}
                  searchQuery={searchQuery}
                  onSearchChange={setSearchQuery}
                  modules={modules}
                  filteredModules={filteredModules}
                  totalsByColumn={totalsByColumn}
                  expandAll={expandAll}
                  collapseAll={collapseAll}
                  toggleModule={toggleModule}
                  toggleTask={toggleTask}
                  taskExpanded={taskExpanded}
                  updateTaskName={updateTaskName}
                  updateTaskField={updateTaskField}
                  addTask={addTask}
                  addSubFeature={addSubFeature}
                  deleteTask={deleteTask}
                  techStack={techStack}
                  resources={resources}
                />
              )}
            </AnimatePresence>
          </TabsContent>

          <TabsContent value="proposals">
            <ProposalsSection
              proposalData={proposalData}
              summaryData={{ timeline: summaryData.timeline, totalHours: summaryData.totalHours }}
            />
          </TabsContent>
        </Tabs>
      </div>

      <FloatingAIAgent modules={modules} setModules={setModules} apiBase={API_BASE} rawApiResponse={rawApiResponse} />
    </div>
  );
}