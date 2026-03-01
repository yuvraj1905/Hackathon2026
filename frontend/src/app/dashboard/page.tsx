"use client";

import { useState, useCallback, useMemo, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, LogOut, Layers, RefreshCw } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import FloatingAIAgent from "@/components/FloatingAIAgent";
import type { Module, SubTask } from "@/types/dashboard";
import {
  ProposalData,
  ResourceRow,
  TechRec,
  calcTotal,
  fmtInt,
} from "@/lib/utils";
import { transformEstimateResponse } from "@/lib/estimateTransform";
import { EstimatesResultsSection } from "../../components/EstimatesResultsSection";
import {
  EstimateInputSection,
  type LoadingStep,
} from "../../components/EstimateInputSection";
import { ProposalsSection } from "../../components/ProposalsSection";
import {
  appendProposalToHistory,
  fetchEstimate,
  fetchProjects,
  logoutApi,
  setLastEstimateRaw,
  takeLastEstimateRaw,
  type StoredProposalSummary,
} from "@/lib/estimateApi";

export default function DashboardPage() {
  const router = useRouter();
  const [showResults, setShowResults] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [modules, setModules] = useState<Module[]>([]);
  const [techStack, setTechStack] = useState<TechRec[]>([]);
  const [resources, setResources] = useState<ResourceRow[]>([]);
  const [summaryData, setSummaryData] = useState({
    domain: "",
    platforms: [] as string[],
    totalHours: 0,
    timeline: "",
    confidence: 0,
  });
  const [techStackStructured, setTechStackStructured] = useState<Record<
    string,
    unknown
  > | null>(null);
  const [proposalData, setProposalData] = useState<ProposalData | null>(null);
  const [proposalsHistory, setProposalsHistory] = useState<
    StoredProposalSummary[]
  >([]);
  const [rawApiResponse, setRawApiResponse] = useState<any>(null);
  const [estimateTableKey, setEstimateTableKey] = useState(0);
  const [taskExpanded, setTaskExpanded] = useState<Record<string, boolean>>({});
  const [expandedSections, setExpandedSections] = useState<
    Record<string, boolean>
  >({});
  const [activeTab, setActiveTab] = useState("estimates");
  const [projectDesc, setProjectDesc] = useState("");
  const [platforms, setPlatforms] = useState<string[]>([]);
  const [timeline, setTimeline] = useState("");
  const [proposalsLoading, setProposalsLoading] = useState(false);
  const [proposalsError, setProposalsError] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState<LoadingStep>("idle");
  const [estimateError, setEstimateError] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    let cancelled = false;
    setProposalsLoading(true);
    setProposalsError(null);
    fetchProjects()
      .then((list) => {
        if (!cancelled) setProposalsHistory(list);
      })
      .catch((err) => {
        if (!cancelled) {
          setProposalsError(err?.message ?? "Failed to load proposals");
          setProposalsHistory([]);
        }
      })
      .finally(() => {
        if (!cancelled) setProposalsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const raw = takeLastEstimateRaw();
    if (!raw) return;
    try {
      const {
        modules: mods,
        techStack: ts,
        techStackStructured: tss,
        resources: res,
        summary,
        proposal,
      } = transformEstimateResponse(raw);
      setModules(mods);
      setTechStack(ts);
      setTechStackStructured(tss);
      setResources(res);
      setSummaryData(summary);
      setProposalData(proposal);
      setRawApiResponse(raw);
      setShowResults(true);
      setActiveTab("estimates");
      fetchProjects()
        .then(setProposalsHistory)
        .catch(() => {});
    } catch {
      // ignore
    }
  }, []);

  const togglePlatform = useCallback((value: string) => {
    setPlatforms((prev) =>
      prev.includes(value) ? prev.filter((p) => p !== value) : [...prev, value],
    );
  }, []);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0] ?? null;
      setUploadedFile(file);
      if (file) toast({ title: `File selected: ${file.name}` });
    },
    [toast],
  );

  const handleFileDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      const file = e.dataTransfer.files?.[0] ?? null;
      setUploadedFile(file);
      if (file) toast({ title: `File selected: ${file.name}` });
    },
    [toast],
  );

  const handleGenerate = useCallback(async () => {
    const desc = projectDesc.trim();
    if (!desc && !uploadedFile) {
      toast({
        title: "Enter a description or upload a file",
        variant: "destructive",
      });
      return;
    }
    if (desc.length > 0 && desc.length < 10) {
      toast({
        title: "Description must be at least 10 characters",
        variant: "destructive",
      });
      return;
    }
    setLoading(true);
    setEstimateError(null);
    setLoadingStep("estimating");
    try {
      toast({ title: "Generating estimation..." });
      const raw = await fetchEstimate({
        project_description: desc || undefined,
        file: uploadedFile || undefined,
        platforms: platforms.length ? platforms : undefined,
        timeline: timeline || undefined,
      });
      appendProposalToHistory(raw, {
        title: projectDesc || uploadedFile?.name,
      });
      setLastEstimateRaw(raw);
      const {
        modules: mods,
        techStack: ts,
        techStackStructured: tss,
        resources: res,
        summary,
        proposal,
      } = transformEstimateResponse(raw);
      setModules(mods);
      setTechStack(ts);
      setTechStackStructured(tss);
      setResources(res);
      setSummaryData(summary);
      setProposalData(proposal);
      setRawApiResponse(raw);
      setShowResults(true);
      setActiveTab("estimates");
      toast({ title: "Estimation ready!" });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "";
      const isNet =
        msg === "Failed to fetch" ||
        msg.includes("NetworkError") ||
        msg.includes("Load failed");
      const userMsg = isNet
        ? "Request did not complete. Estimation can take 1–2 minutes—try again or check the backend."
        : msg || "Estimation failed.";
      setEstimateError(userMsg);
      toast({
        title: "Estimation failed",
        description: userMsg,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
      setLoadingStep("idle");
    }
  }, [projectDesc, platforms, timeline, uploadedFile, toast]);

  const toggleModule = useCallback(
    (id: string) =>
      setModules((p) =>
        p.map((m) => (m.id === id ? { ...m, expanded: !m.expanded } : m)),
      ),
    [],
  );
  const toggleTask = useCallback(
    (id: string) => setTaskExpanded((p) => ({ ...p, [id]: !p[id] })),
    [],
  );
  const expandAll = useCallback(() => {
    setModules((p) => p.map((m) => ({ ...m, expanded: true })));
    setTaskExpanded((prev) => {
      const taskIdsWithChildren = modules.flatMap((m) =>
        m.tasks.filter((t) => (t.children?.length ?? 0) > 0).map((t) => t.id),
      );
      return {
        ...prev,
        ...Object.fromEntries(taskIdsWithChildren.map((id) => [id, true])),
      };
    });
  }, [modules]);
  const collapseAll = useCallback(() => {
    setModules((p) => p.map((m) => ({ ...m, expanded: false })));
    setTaskExpanded({});
  }, []);
  const toggleSection = (key: string) =>
    setExpandedSections((p) => ({ ...p, [key]: !p[key] }));

  const handleClearResults = useCallback(() => {
    setShowResults(false);
    setModules([]);
    setTechStack([]);
    setResources([]);
    setSummaryData({
      domain: "",
      platforms: [],
      totalHours: 0,
      timeline: "",
      confidence: 0,
    });
    setTechStackStructured(null);
    setProposalData(null);
    setRawApiResponse(null);
    setTaskExpanded({});
    setSearchQuery("");
    setExpandedSections({});
    setActiveTab("proposals");
  }, []);

  const updateTaskField = useCallback(
    (
      moduleId: string,
      taskId: string,
      field: "frontend" | "backend" | "integration" | "testing",
      value: number,
      childId?: string,
    ) => {
      setModules((prev) =>
        prev.map((m) => {
          if (m.id !== moduleId) return m;
          return {
            ...m,
            tasks: m.tasks.map((t) => {
              if (childId && t.id === taskId) {
                const kids = t.children?.map((c) => {
                  if (c.id !== childId) return c;
                  const u = { ...c, [field]: value };
                  u.total = calcTotal(u);
                  return u;
                });
                const p = { ...t, children: kids };
                if (kids?.length) {
                  p.frontend = kids.reduce((a, c) => a + c.frontend, 0);
                  p.backend = kids.reduce((a, c) => a + c.backend, 0);
                  p.integration = kids.reduce(
                    (a, c) => a + (c.integration ?? 0),
                    0,
                  );
                  p.testing = kids.reduce((a, c) => a + c.testing, 0);
                  p.total = calcTotal(p);
                }
                return p;
              }
              if (t.id !== taskId) return t;
              const u = { ...t, [field]: value };
              u.total = calcTotal(u);
              return u;
            }),
          };
        }),
      );
    },
    [],
  );

  const updateTaskName = useCallback(
    (moduleId: string, taskId: string, name: string, childId?: string) => {
      setModules((prev) =>
        prev.map((m) => {
          if (m.id !== moduleId) return m;
          return {
            ...m,
            tasks: m.tasks.map((t) => {
              if (childId && t.id === taskId)
                return {
                  ...t,
                  children: t.children?.map((c) =>
                    c.id === childId ? { ...c, name } : c,
                  ),
                };
              if (t.id === taskId) return { ...t, name };
              return t;
            }),
          };
        }),
      );
    },
    [],
  );

  const deleteTask = useCallback(
    (moduleId: string, taskId: string, childId?: string) => {
      setModules((prev) =>
        prev.map((m) => {
          if (m.id !== moduleId) return m;
          if (childId) {
            return {
              ...m,
              tasks: m.tasks.map((t) => {
                if (t.id !== taskId) return t;
                const kids = t.children?.filter((c) => c.id !== childId);
                const u = { ...t, children: kids };
                if (kids?.length) {
                  u.frontend = kids.reduce((a, c) => a + c.frontend, 0);
                  u.backend = kids.reduce((a, c) => a + c.backend, 0);
                  u.integration = kids.reduce(
                    (a, c) => a + (c.integration ?? 0),
                    0,
                  );
                  u.testing = kids.reduce((a, c) => a + c.testing, 0);
                  u.total = calcTotal(u);
                }
                return u;
              }),
            };
          }
          return {
            ...m,
            tasks: m.tasks.filter((t) => t.id !== taskId),
          };
        }),
      );
      toast({ title: "Deleted" });
    },
    [toast],
  );

  const addSubFeature = useCallback(
    (moduleId: string, taskId: string) => {
      setModules((prev) =>
        prev.map((m) => {
          if (m.id !== moduleId) return m;
          return {
            ...m,
            tasks: m.tasks.map((t) => {
              if (t.id !== taskId) return t;
              const child: SubTask = {
                id: `${t.id}.${(t.children?.length || 0) + 1}`,
                name: "New sub-feature",
                frontend: 0,
                backend: 0,
                integration: 0,
                testing: 0,
                total: 0,
              };
              return {
                ...t,
                children: [...(t.children || []), child],
              };
            }),
          };
        }),
      );
      setTaskExpanded((p) => ({ ...p, [taskId]: true }));
      toast({ title: "Sub-feature added" });
    },
    [toast],
  );

  const addTask = useCallback(
    (moduleId: string) => {
      setModules((prev) =>
        prev.map((m) => {
          if (m.id !== moduleId) return m;
          const task: SubTask = {
            id: `${m.id}.${m.tasks.length + 1}`,
            name: "New feature",
            frontend: 0,
            backend: 0,
            integration: 0,
            testing: 0,
            total: 0,
          };
          return { ...m, tasks: [...m.tasks, task], expanded: true };
        }),
      );
      toast({ title: "Feature added" });
    },
    [toast],
  );

  const filteredModules = useMemo(() => {
    if (!searchQuery.trim()) return modules;
    const q = searchQuery.toLowerCase();
    return modules
      .map((m) => ({
        ...m,
        tasks: m.tasks.filter(
          (t) =>
            t.name.toLowerCase().includes(q) ||
            m.name.toLowerCase().includes(q),
        ),
      }))
      .filter((m) => m.name.toLowerCase().includes(q) || m.tasks.length > 0);
  }, [modules, searchQuery]);

  const totalsByColumn = useMemo(
    () =>
      modules.reduce(
        (acc, m) => {
          m.tasks.forEach((t) => {
            acc.frontend += t.frontend;
            acc.backend += t.backend;
            acc.integration += t.integration ?? 0;
            acc.testing += t.testing;
            acc.total += t.total;
          });
          return acc;
        },
        {
          frontend: 0,
          backend: 0,
          integration: 0,
          testing: 0,
          total: 0,
        },
      ),
    [modules],
  );

  const featureCount = useMemo(
    () => modules.reduce((a, m) => a + m.tasks.length, 0),
    [modules],
  );

  const statCards = useMemo(
    () => [
      {
        label: "Estimation Hours",
        value: fmtInt(totalsByColumn.total),
        meta: `${modules.length} modules · ${featureCount} features`,
        color: "text-foreground",
        iconColor: "text-primary",
        bg: "stat-blue",
        icon: Layers,
      },
    ],
    [totalsByColumn, modules.length, featureCount],
  );

  /* ═══════════════════════════════════════════════════════════════════════
   RENDER
   ═══════════════════════════════════════════════════════════════════════ */
  return (
    <div className="min-h-screen relative bg-background">
      {/* ── Ambient background ──────────────────────────────────────── */}
      <div className="fixed inset-0 pointer-events-none z-0 dot-grid opacity-30" />
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div
          className="absolute top-[-12%] right-[-8%] w-[550px] h-[550px] rounded-full opacity-60"
          style={{
            background:
              "radial-gradient(circle, hsl(230 94% 68% / 0.1), transparent 55%)",
            filter: "blur(90px)",
            animation: "aurora-float 20s ease-in-out infinite alternate",
          }}
        />
        <div
          className="absolute bottom-[5%] left-[-6%] w-[450px] h-[450px] rounded-full opacity-50"
          style={{
            background:
              "radial-gradient(circle, hsl(270 88% 68% / 0.08), transparent 55%)",
            filter: "blur(90px)",
            animation:
              "aurora-float 16s ease-in-out infinite alternate-reverse",
          }}
        />
      </div>

      {/* ── Navbar ──────────────────────────────────────────────────── */}
      <nav
        className="sticky top-0 z-40 border-b border-border/30"
        style={{
          background: "hsl(var(--card) / 0.6)",
          backdropFilter: "blur(20px) saturate(1.5)",
        }}
      >
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/20 to-transparent pointer-events-none" />
        <div className="container mx-auto flex items-center justify-between h-14 px-4">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="w-9 h-9 rounded-xl gradient-bg flex items-center justify-center shrink-0 shadow-lg shadow-primary/25 group-hover:shadow-primary/40 group-hover:scale-105 transition-all duration-300">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <span
                className="text-lg font-bold hidden sm:block tracking-tight"
                style={{ fontFamily: "'Sora', system-ui" }}
              >
                Neural Architects
              </span>
            </Link>
            {showResults && summaryData.domain && (
              <motion.div
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                className="hidden md:flex items-center gap-1.5 ml-3 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/15"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-[11px] font-semibold text-emerald-400 capitalize">
                  {summaryData.domain}
                </span>
              </motion.div>
            )}
          </div>
          <div className="flex items-center gap-2">
            {showResults && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleClearResults}
                className="rounded-xl border-border/40 hover:border-primary/30 hover:bg-primary/5 text-xs font-medium"
              >
                <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Clear
              </Button>
            )}
            <ThemeToggle
              inline
              className="h-8 w-8 rounded-xl border-border/40 hover:bg-primary/5"
            />
            <Button
              variant="ghost"
              size="sm"
              className="rounded-xl text-muted-foreground hover:text-foreground"
              onClick={async () => {
                await logoutApi();
                if (typeof window !== "undefined") {
                  window.localStorage.removeItem("authToken");
                  window.localStorage.removeItem("authUser");
                }
                router.push("/");
              }}
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </nav>

      {/* ── Main ───────────────────────────────────────────────────── */}
      <div className="container mx-auto px-4 py-8 relative z-10">
        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="space-y-6"
        >
          <div className="flex items-center justify-between">
            <TabsList>
              <TabsTrigger value="proposals">Proposals</TabsTrigger>
              <TabsTrigger value="estimates">Estimates</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="proposals">
            <ProposalsSection
              proposalData={proposalData}
              summaryData={{
                timeline: summaryData.timeline,
                totalHours: summaryData.totalHours,
              }}
              proposals={proposalsHistory}
            />
          </TabsContent>

          <TabsContent value="estimates">
            <AnimatePresence mode="wait">
              {!showResults ? (
                <EstimateInputSection
                  projectDesc={projectDesc}
                  platforms={platforms}
                  timeline={timeline}
                  uploadedFile={uploadedFile}
                  loading={loading}
                  loadingStep={loadingStep}
                  error={estimateError}
                  onChangeProjectDesc={setProjectDesc}
                  onTogglePlatform={togglePlatform}
                  onChangeTimeline={setTimeline}
                  onFileChange={handleFileChange}
                  onFileDrop={handleFileDrop}
                  onGenerate={handleGenerate}
                />
              ) : (
                <>
                  <EstimatesResultsSection
                    estimateTableKey={estimateTableKey}
                    statCards={statCards}
                    summaryData={summaryData}
                    proposalData={proposalData}
                    currentProjectId={rawApiResponse?.project_id ?? null}
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
                    techStackStructured={techStackStructured}
                    resources={resources}
                  />
                  {modules.length > 0 && (
                    <FloatingAIAgent
                      modules={modules}
                      setModules={setModules}
                      onModifyApplied={() => setEstimateTableKey((k) => k + 1)}
                      apiBase={process.env.NEXT_PUBLIC_API_BASE}
                      rawApiResponse={rawApiResponse}
                    />
                  )}
                </>
              )}
            </AnimatePresence>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
