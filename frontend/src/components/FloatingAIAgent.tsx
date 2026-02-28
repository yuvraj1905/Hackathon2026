"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, Send, X, Loader2, Minimize2, Maximize2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import type { Module, SubTask } from "@/types/dashboard";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface FloatingAIAgentProps {
  modules: Module[];
  setModules: React.Dispatch<React.SetStateAction<Module[]>>;
  onModifyApplied?: () => void;
  apiBase?: string;
  rawApiResponse?: any;
}

function getPhaseRatiosFromContext(context: any) {
  if (!context || typeof context !== "object") return null;
  const planning = context.planning || context.context?.planning;
  const phaseSplit = planning?.phase_split;
  if (!phaseSplit || typeof phaseSplit !== "object") return null;

  const f = Number((phaseSplit as any).frontend) || 0;
  const b = Number((phaseSplit as any).backend) || 0;
  const qa = Number((phaseSplit as any).qa) || 0;
  const total = f + b + qa;
  if (total <= 0) return null;

  return {
    frontend: f / total,
    backend: b / total,
    testing: qa / total,
  };
}

function getPhaseRatiosFromModules(modules: Module[]) {
  let fe = 0, be = 0, test = 0;
  for (const m of modules) {
    for (const t of m.tasks) {
      fe += t.frontend;
      be += t.backend;
      test += t.testing;
    }
  }
  const total = fe + be + test;
  if (total <= 0) return null;
  return {
    frontend: fe / total,
    backend: be / total,
    testing: test / total,
  };
}

function parseModifyResponse(data: any, context?: any, currentModules?: Module[]): Module[] | null {
  // Modify API response: apply whenever we have a features array (single source of truth)
  const hasFeatures =
    data &&
    Array.isArray(data.features) &&
    data.features.length > 0;

  if (hasFeatures) {
    const features: any[] = data.features;

    // Use only API/context or current table ratios; if none, put hours in integration only
    const ratios =
      getPhaseRatiosFromContext(context) ??
      getPhaseRatiosFromModules(currentModules ?? []) ?? {
        frontend: 0,
        backend: 0,
        testing: 0,
      };

    function splitHours(hours: number) {
      const fe = Math.round(hours * ratios!.frontend * 10) / 10;
      const be = Math.round(hours * ratios!.backend * 10) / 10;
      const test = Math.round(hours * ratios!.testing * 10) / 10;
      const integ = Math.max(0, Math.round((hours - fe - be - test) * 10) / 10);
      return { fe, be, test, integ };
    }

    const tasks: SubTask[] = features.map((f: any, i: number) => {
      const hours = Number(f.total_hours ?? f.estimated_hours) || 0;
      const { fe, be, test, integ } = splitHours(hours);
      const complexity = (f.complexity || "").toString().toLowerCase() || undefined;
      const featureName = (f.name ?? "").toString().trim();
      const subfeatures: any[] = Array.isArray(f.subfeatures) ? f.subfeatures : [];
      let children: SubTask[] | undefined =
        subfeatures.length > 0
          ? subfeatures.map((sf: any, j: number) => {
              const eff = Number(sf.effort) || 0;
              const s = splitHours(eff);
              return {
                id: `${i + 1}-${j + 1}`,
                name: (sf.name ?? "").toString().trim(),
                frontend: s.fe,
                backend: s.be,
                integration: s.integ,
                testing: s.test,
                total: eff,
                ...(complexity ? { complexity } : {}),
              };
            })
          : undefined;
      if (children?.length === 1 && children[0].name.toLowerCase() === featureName.toLowerCase()) {
        children = undefined;
      }
      return {
        id: String(i + 1),
        name: featureName,
        frontend: fe,
        backend: be,
        integration: integ,
        testing: test,
        total: hours,
        ...(complexity ? { complexity } : {}),
        children,
      };
    });

    // Module name only from API context (domain_detection from original estimate)
    const domainDetection = context?.domain_detection || context?.context?.domain_detection;
    const domainStr = (domainDetection?.detected_domain ?? "").toString().replace(/_/g, " ").trim();
    const moduleName = domainStr
      ? domainStr.charAt(0).toUpperCase() + domainStr.slice(1)
      : "";

    return [
      {
        id: "1",
        name: moduleName,
        expanded: true,
        tasks,
      },
    ];
  }

  // Nested response (e.g. main estimate): modules or estimation.modules/estimation.features
  const rawModules: any[] =
    data?.modules ?? data?.estimation?.modules ?? data?.estimation?.features ?? [];

  if (!rawModules || rawModules.length === 0) return null;

    return rawModules.map((mod: any, idx: number) => {
    const moduleId = String(mod.id ?? idx + 1);
    const rawTasks: any[] = mod.tasks ?? mod.sub_features ?? mod.subFeatures ?? mod.features ?? [];

    const tasks: SubTask[] = rawTasks.map((task: any, tIdx: number) => {
      const taskId = String(task.id ?? `${moduleId}.${tIdx + 1}`);
      const fe = task.frontend ?? task.frontend_hours ?? task.fe_hours ?? 0;
      const be = task.backend ?? task.backend_hours ?? task.be_hours ?? 0;
      const test = task.testing ?? task.testing_hours ?? task.qa_hours ?? 0;

      const rawChildren: any[] = task.children ?? task.sub_features ?? task.subFeatures ?? [];
      const children: SubTask[] | undefined =
        rawChildren.length > 0
          ? rawChildren.map((child: any, cIdx: number) => {
            const cFe = child.frontend ?? child.frontend_hours ?? child.fe_hours ?? 0;
            const cBe = child.backend ?? child.backend_hours ?? child.be_hours ?? 0;
            const cTest = child.testing ?? child.testing_hours ?? child.qa_hours ?? 0;
            return {
              id: String(child.id ?? `${taskId}.${cIdx + 1}`),
              name: (child.name ?? child.title ?? "").toString().trim(),
              frontend: cFe,
              backend: cBe,
              integration: 0,
              testing: cTest,
              total: cFe + cBe + cTest,
            };
          })
          : undefined;

      return {
        id: taskId,
        name: (task.name ?? task.title ?? "").toString().trim(),
        frontend: fe,
        backend: be,
        integration: 0,
        testing: test,
        total: fe + be + test,
        children,
      };
    });

    return {
      id: moduleId,
      name: (mod.name ?? mod.title ?? mod.module ?? "").toString().trim(),
      expanded: idx === 0,
      tasks,
    };
  });
}

export default function FloatingAIAgent({ modules, setModules, onModifyApplied, apiBase, rawApiResponse }: FloatingAIAgentProps) {
  const API_BASE = apiBase || "http://127.0.0.1:8000";

  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Hi! I'm your AI estimation assistant. You can ask me to modify the estimation — for example:\n\n• \"Add a chat module with real-time messaging\"\n• \"Increase backend hours for the booking flow\"\n• \"Remove the notifications module\"\n• \"Add payment gateway integration\"",
      timestamp: new Date(),
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && !isMinimized) {
      setTimeout(() => inputRef.current?.focus(), 200);
    }
  }, [isOpen, isMinimized]);

  const handleSend = async () => {
    const prompt = input.trim();
    if (!prompt || loading) return;

    // Add user message
    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: prompt,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      type FeaturePayload = { name: string; category: string; complexity: string; subfeatures: Array<{ name: string }> };
      let currentFeatures: FeaturePayload[] = [];

      const estimationFeatures = rawApiResponse?.estimation?.features && Array.isArray(rawApiResponse.estimation.features)
        ? rawApiResponse.estimation.features
        : [];
      const richSubfeaturesByFeatureName: Record<string, Array<{ name: string }>> = {};
      for (const f of estimationFeatures) {
        const fName = (f.name || "").toString().trim();
        if (!fName) continue;
        const subfeaturesRaw = f.subfeatures || [];
        const list = subfeaturesRaw.map((sf: any) => ({ name: (sf.name || "").toString().trim() })).filter((s: { name: string }) => s.name);
        const isSingleSelfNamed = list.length === 1 && (list[0].name || "").toLowerCase() === fName.toLowerCase();
        const toStore = list.length === 0 || isSingleSelfNamed ? [] : list;
        if (toStore.length > 0) richSubfeaturesByFeatureName[fName.toLowerCase()] = toStore;
      }

      const hasModulesWithTasks = modules.some((m) => m.tasks.length > 0);
      if (hasModulesWithTasks) {
        currentFeatures = modules.flatMap((m) =>
          m.tasks.map((t) => {
            const children = t.children || [];
            const isSingleSelfNamed =
              children.length === 1 &&
              (children[0].name || "").trim().toLowerCase() === (t.name || "").trim().toLowerCase();
            let subfeatures =
              children.length === 0 || isSingleSelfNamed
                ? []
                : children.map((c) => ({ name: c.name }));
            const rich = richSubfeaturesByFeatureName[(t.name || "").trim().toLowerCase()];
            if (rich && rich.length > subfeatures.length) subfeatures = rich;
            return {
              name: t.name,
              category: "Core",
              complexity: (t.complexity || "medium").toString(),
              subfeatures,
            };
          }),
        );
      } else if (estimationFeatures.length > 0) {
        currentFeatures = estimationFeatures.map((f: any) => {
          const fName = (f.name || "").toString().trim();
          const subfeaturesRaw = f.subfeatures || [];
          const subfeatures = subfeaturesRaw.map((sf: any) => ({ name: (sf.name || "").toString().trim() })).filter((s: { name: string }) => s.name);
          const isSingleSelfNamed =
            subfeatures.length === 1 && (subfeatures[0].name || "").toLowerCase() === fName.toLowerCase();
          const toSend = subfeatures.length === 0 || isSingleSelfNamed ? [] : subfeatures;
          return {
            name: fName,
            category: (f.description || f.category || "Core").toString(),
            complexity: (f.complexity || "medium").toString(),
            subfeatures: toSend,
          };
        });
      }

      if (currentFeatures.length === 0) {
        throw new Error("No features available to modify. Please generate an estimation first.");
      }

      const response = await fetch(`${API_BASE}/modify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          current_features: currentFeatures,
          instruction: prompt,
        }),
      });

      if (!response.ok) {
        const errText = await response.text().catch(() => "");
        throw new Error(`API Error ${response.status}: ${errText || response.statusText}`);
      }

      const data = await response.json();

      // Modify API is the single source of truth: build table data directly from API features (including subfeatures)
      // Support both "features" and "estimated_features" in case API response shape changes
      const rawFeatures = Array.isArray(data.features) ? data.features : Array.isArray(data.estimated_features) ? data.estimated_features : [];
      if (rawFeatures.length > 0) {
        const features: any[] = rawFeatures;
        const tasks: SubTask[] = features.map((f: any, i: number) => {
          const hours = Number(f.total_hours ?? f.estimated_hours) || 0;
          const third = Math.round((hours / 3) * 10) / 10;
          const featureName = (f.name ?? "").toString().trim() || `Feature ${i + 1}`;
          const subfeaturesRaw: any[] = Array.isArray(f.subfeatures) ? f.subfeatures : [];
          // Don't show a single self-named subfeature (e.g. "Logout" under "Logout") as children
          const subList = subfeaturesRaw
            .map((sf: any, j: number) => ({
              id: `modify-${i + 1}-${j + 1}`,
              name: (sf.name ?? "").toString().trim(),
              effort: Number(sf.effort) || 0,
            }))
            .filter((s) => s.name && s.name.toLowerCase() !== featureName.toLowerCase());
          const children: SubTask[] | undefined =
            subList.length > 0
              ? subList.map((s) => {
                  const e = s.effort;
                  const t = Math.round((e / 3) * 10) / 10;
                  return {
                    id: s.id,
                    name: s.name,
                    frontend: t,
                    backend: t,
                    integration: 0,
                    testing: Math.round((e - t * 2) * 10) / 10,
                    total: e,
                  };
                })
              : undefined;
          return {
            id: `modify-${i + 1}`,
            name: featureName,
            frontend: third,
            backend: third,
            integration: 0,
            testing: Math.round((hours - third * 2) * 10) / 10,
            total: hours,
            ...(children && children.length > 0 ? { children } : {}),
            ...((f.complexity && String(f.complexity).toLowerCase()) ? { complexity: String(f.complexity).toLowerCase() } : {}),
          };
        });
        const domainStr = (rawApiResponse?.domain_detection?.detected_domain ?? "").toString().replace(/_/g, " ").trim();
        const moduleName = domainStr ? domainStr.charAt(0).toUpperCase() + domainStr.slice(1) : "Features";
        const updatedModules: Module[] = [{ id: "modify-1", name: moduleName, expanded: true, tasks }];
        setModules(updatedModules);
        onModifyApplied?.();
      }

      // Use only backend response: changes_summary and hours (no fallback copy)
      const parts: string[] = [];
      if (typeof data.changes_summary === "string" && data.changes_summary.trim()) {
        parts.push(data.changes_summary.trim());
      }
      if (typeof data.total_hours === "number") {
        parts.push(`Total: ${data.total_hours} hrs`);
        if (typeof data.min_hours === "number" && typeof data.max_hours === "number") {
          parts.push(`Range: ${data.min_hours}–${data.max_hours} hrs`);
        }
      }
      const assistantContent = parts.length > 0 ? parts.join("\n\n") : "";

      if (assistantContent !== "") {
        const assistantMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: assistantContent,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
      }

      toast({ title: "Estimation updated!" });
    } catch (err: any) {
      console.error("Modify API error:", err);

      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Sorry, I encountered an error: ${err.message}. Please try again.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);

      toast({
        title: "Modification failed",
        description: err.message,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <AnimatePresence>
        {!isOpen && (
          <motion.button
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            whileHover={{ scale: 1.12 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => setIsOpen(true)}
            className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full gradient-bg flex items-center justify-center text-white"
            style={{ boxShadow: "0 0 20px hsl(217 95% 65% / 0.45), 0 4px 20px hsl(217 95% 65% / 0.25)" }}
          >
            {/* Pulse rings */}
            <span className="absolute inset-0 rounded-full animate-ping opacity-20"
              style={{ background: "hsl(217 95% 65%)" }} />
            <Bot className="w-6 h-6 relative z-10" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* ── Chat Panel ─────────────────────────────────────────────────── */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 24, scale: 0.92 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            className="fixed bottom-6 right-6 z-50 w-[400px] max-h-[560px] rounded-2xl border border-primary/20 bg-card/90 backdrop-blur-xl shadow-2xl shadow-black/40 flex flex-col overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-border/40 bg-muted/20">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl gradient-bg flex items-center justify-center shadow-sm shadow-primary/30">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div>
                  <p className="text-sm font-semibold">AI Assistant</p>
                  <p className="text-[10px] text-muted-foreground flex items-center gap-1">
                    {loading ? (
                      <><span className="w-1.5 h-1.5 rounded-full bg-warning animate-pulse" /> Thinking...</>
                    ) : (
                      <><span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" /> Ready to modify</>
                    )}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setIsMinimized(!isMinimized)}
                  className="p-1.5 hover:bg-muted rounded-md transition-colors"
                >
                  {isMinimized ? <Maximize2 className="w-3.5 h-3.5" /> : <Minimize2 className="w-3.5 h-3.5" />}
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1.5 hover:bg-muted rounded-md transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {!isMinimized && (
              <>
                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-[300px] max-h-[400px]">
                  {messages.map((msg) => (
                    <motion.div
                      key={msg.id}
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`max-w-[85%] rounded-xl px-3.5 py-2.5 text-sm leading-relaxed ${msg.role === "user"
                            ? "gradient-bg text-primary-foreground"
                            : "bg-muted/50 text-foreground border border-border/30"
                          }`}
                      >
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                        <p
                          className={`text-[10px] mt-1 ${msg.role === "user" ? "text-primary-foreground/60" : "text-muted-foreground"
                            }`}
                        >
                          {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </p>
                      </div>
                    </motion.div>
                  ))}

                  {/* Loading indicator */}
                  {loading && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
                      <div className="bg-muted/50 border border-border/30 rounded-xl px-4 py-3 flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin text-primary" />
                        <span className="text-sm text-muted-foreground">Processing modification...</span>
                      </div>
                    </motion.div>
                  )}

                  <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <div className="p-3 border-t border-border/40 bg-muted/10">
                  <div className="flex items-center gap-2">
                    <input
                      ref={inputRef}
                      type="text"
                      placeholder="Ask to modify the estimation..."
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault();
                          handleSend();
                        }
                      }}
                      disabled={loading}
                      className="flex-1 h-9 px-3 rounded-lg border border-border/40 bg-background/50 text-sm focus:outline-none focus:ring-1 focus:ring-primary/60 disabled:opacity-50 placeholder:text-muted-foreground/60"
                    />
                    <Button
                      size="sm"
                      onClick={handleSend}
                      disabled={loading || !input.trim()}
                      className="btn-glow text-white h-9 w-9 p-0 disabled:opacity-40 disabled:shadow-none"
                    >
                      {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                    </Button>
                  </div>
                </div>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
