"use client";

import React, { Fragment } from "react";
import { motion } from "framer-motion";
import {
  ChevronDown,
  ChevronRight,
  Download,
  Plus,
  Search,
  Share2,
  Trash2,
  CheckCircle,
  TestTube,
  Clock,
  Code2,
  Users,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import type { Module } from "@/types/dashboard";
import { ProposalData, ResourceRow, TechRec, calcTotal, complexityBadge, fmtNum } from "@/lib/utils";

interface EditableCellProps {
  value: number;
  onChange: (v: number) => void;
}

const EditableCell = ({ value, onChange }: EditableCellProps) => {
  const [editing, setEditing] = React.useState(false);
  const [val, setVal] = React.useState(String(value));

  const commit = React.useCallback(
    (v: string) => {
      const n = parseFloat(v);
      onChange(Number.isNaN(n) ? 0 : Math.round(n * 100) / 100);
      setEditing(false);
    },
    [onChange],
  );

  if (editing) {
    return (
      <input
        type="number"
        autoFocus
        className="h-7 w-16 rounded-lg border border-primary/50 bg-background/80 text-center text-sm font-medium shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
        value={val}
        onChange={(e) => setVal(e.target.value)}
        onBlur={() => commit(val)}
        onKeyDown={(e) => {
          if (e.key === "Enter") commit(val);
          if (e.key === "Escape") setEditing(false);
        }}
      />
    );
  }

  return (
    <span
      className="inline-block min-w-[2.5rem] cursor-pointer rounded-lg px-2 py-1 text-center text-sm font-medium font-mono transition-all duration-200 hover:bg-primary/8 hover:text-primary"
      onClick={() => {
        setVal(String(value));
        setEditing(true);
      }}
      title="Click to edit"
    >
      {fmtNum(value)}
    </span>
  );
};

interface EditableNameCellProps {
  value: string;
  onChange: (v: string) => void;
  className?: string;
}

const EditableNameCell = ({
  value,
  onChange,
  className = "",
}: EditableNameCellProps) => {
  const [editing, setEditing] = React.useState(false);
  const [val, setVal] = React.useState(value);

  const commit = React.useCallback(
    (v: string) => {
      onChange(v);
      setEditing(false);
    },
    [onChange],
  );

  if (editing) {
    return (
      <input
        type="text"
        autoFocus
        className={`h-7 w-full max-w-[260px] rounded-lg border border-primary/50 bg-background/80 px-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/30 ${className}`}
        value={val}
        onChange={(e) => setVal(e.target.value)}
        onBlur={() => commit(val)}
        onKeyDown={(e) => {
          if (e.key === "Enter") commit(val);
          if (e.key === "Escape") setEditing(false);
        }}
      />
    );
  }

  return (
    <span
      className={`cursor-pointer rounded-lg px-1.5 py-0.5 text-sm transition-all duration-200 hover:bg-primary/8 hover:text-primary ${className}`}
      onClick={() => {
        setVal(value);
        setEditing(true);
      }}
      title="Click to edit"
    >
      {value}
    </span>
  );
};

interface EstimatesResultsSectionProps {
  statCards: {
    label: string;
    value: string;
    meta?: string;
    color: string;
    iconColor: string;
    bg: string;
    icon: React.ElementType;
  }[];
  summaryData: { domain: string; totalHours: number; timeline: string; confidence: number };
  proposalData: ProposalData | null;
  searchQuery: string;
  onSearchChange: (v: string) => void;
  modules: Module[];
  filteredModules: Module[];
  totalsByColumn: {
    frontend: number;
    backend: number;
    integration: number;
    testing: number;
    total: number;
  };
  expandAll: () => void;
  collapseAll: () => void;
  toggleModule: (id: string) => void;
  toggleTask: (id: string) => void;
  taskExpanded: Record<string, boolean>;
  updateTaskName: (
    moduleId: string,
    taskId: string,
    name: string,
    childId?: string,
  ) => void;
  updateTaskField: (
    moduleId: string,
    taskId: string,
    field: "frontend" | "backend" | "integration" | "testing",
    value: number,
    childId?: string,
  ) => void;
  addTask: (moduleId: string) => void;
  addSubFeature: (moduleId: string, taskId: string) => void;
  deleteTask: (moduleId: string, taskId: string, childId?: string) => void;
  techStack: TechRec[];
  resources: ResourceRow[];
}

export function EstimatesResultsSection({
  statCards,
  summaryData,
  proposalData,
  searchQuery,
  onSearchChange,
  modules,
  filteredModules,
  totalsByColumn,
  expandAll,
  collapseAll,
  toggleModule,
  toggleTask,
  taskExpanded,
  updateTaskName,
  updateTaskField,
  addTask,
  addSubFeature,
  deleteTask,
  techStack,
  resources,
}: EstimatesResultsSectionProps) {
  const featureCount = modules.reduce((a, m) => a + m.tasks.length, 0);

  return (
    <motion.div
      key="results"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="space-y-7"
    >
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        {statCards.map((s, i) => {
          const Icon = s.icon;
          return (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                delay: i * 0.08,
                duration: 0.5,
                ease: [0.22, 1, 0.36, 1],
              }}
              className={`stat-bento shine-hover ${s.bg} ${i === 0
                  ? "lg:col-span-2 lg:flex-row lg:items-center lg:gap-6 lg:min-h-[140px]"
                  : ""
                }`}
            >
              <div
                className={`stat-icon-wrap rounded-xl ${i === 0 ? "lg:mb-0 lg:h-14 lg:w-14" : ""
                  }`}
              >
                <Icon
                  className={`h-6 w-6 ${s.iconColor} ${i === 0 ? "lg:h-7 lg:w-7" : ""
                    }`}
                />
              </div>
              <div className={i === 0 ? "lg:flex-1" : ""}>
                <span
                  className={`stat-value ${s.color} ${i === 0 ? "lg:text-4xl xl:text-5xl" : ""
                    }`}
                >
                  {s.value}
                </span>
                <span className="stat-label mt-1 block">{s.label}</span>
                {s.meta && <span className="stat-meta block">{s.meta}</span>}
              </div>
            </motion.div>
          );
        })}
      </div>

      {(summaryData.domain || summaryData.timeline || summaryData.confidence > 0) && (
        <div className="pill-group">
          {summaryData.domain && (
            <span className="pill-primary capitalize">{summaryData.domain}</span>
          )}
          {summaryData.timeline && (
            <span className="pill-muted">
              <Clock className="mr-1 h-3 w-3" />
              {summaryData.timeline}
            </span>
          )}
          {summaryData.confidence > 0 && (
            <span className="pill-accent">{summaryData.confidence}% confidence</span>
          )}
          {proposalData && proposalData.minHours > 0 && (
            <span className="pill-muted">
              {fmtNum(proposalData.minHours)}–{fmtNum(proposalData.maxHours)} hrs range
            </span>
          )}
        </div>
      )}

      <div className="flex flex-col items-stretch justify-between gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1 max-w-sm">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground/50" />
          <Input
            placeholder="Search features…"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="h-10 rounded-xl border-border/40 bg-card/40 pl-10 focus:ring-2 focus:ring-primary/20"
          />
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={expandAll}
            className="rounded-xl border-border/40 text-xs hover:border-primary/25 hover:bg-primary/5"
          >
            Expand All
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={collapseAll}
            className="rounded-xl border-border/40 text-xs hover:border-primary/25 hover:bg-primary/5"
          >
            Collapse All
          </Button>
        </div>
      </div>

      {filteredModules.length > 0 ? (
        <div className="card-spotlight table-premium overflow-hidden rounded-2xl">
          <div className="overflow-x-auto">
            <table className="estimation-table">
              <thead>
                <tr>
                  <th className="w-10 text-center">#</th>
                  <th className="min-w-[150px]">Module</th>
                  <th className="min-w-[200px]">Feature</th>
                  <th className="w-20 text-center">FE hrs</th>
                  <th className="w-20 text-center">BE hrs</th>
                  <th className="w-24 text-center">Integ.</th>
                  <th className="w-20 text-center">Test</th>
                  <th className="w-20 text-center text-primary">Total</th>
                  <th className="w-20 text-center">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredModules.map((mod, modIdx) => {
                  const offset = filteredModules
                    .slice(0, modIdx)
                    .reduce((a, m) => a + m.tasks.length, 0);
                  return (
                    <Fragment key={`mod-${mod.id}`}>
                      <tr
                        className="module-row cursor-pointer"
                        onClick={() => toggleModule(mod.id)}
                      >
                        <td className="text-center text-xs font-mono text-muted-foreground">
                          {mod.id}
                        </td>
                        <td colSpan={2}>
                          <div className="flex items-center gap-2">
                            {mod.expanded ? (
                              <ChevronDown className="h-4 w-4 shrink-0 text-primary/60" />
                            ) : (
                              <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
                            )}
                            <span className="font-bold">{mod.name}</span>
                            <span className="rounded-full bg-muted/30 px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                              {mod.tasks.length} features
                            </span>
                          </div>
                        </td>
                        <td className="text-center text-sm font-medium font-mono">
                          {fmtNum(mod.tasks.reduce((a, t) => a + t.frontend, 0))}
                        </td>
                        <td className="text-center text-sm font-medium font-mono">
                          {fmtNum(mod.tasks.reduce((a, t) => a + t.backend, 0))}
                        </td>
                        <td className="text-center text-sm font-medium font-mono">
                          {fmtNum(mod.tasks.reduce((a, t) => a + (t.integration ?? 0), 0))}
                        </td>
                        <td className="text-center text-sm font-medium font-mono">
                          {fmtNum(mod.tasks.reduce((a, t) => a + t.testing, 0))}
                        </td>
                        <td className="text-center font-mono text-sm font-bold text-primary">
                          {fmtNum(mod.tasks.reduce((a, t) => a + t.total, 0))}
                        </td>
                        <td className="text-center">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              addTask(mod.id);
                            }}
                            className="rounded-lg p-1 text-primary/60 transition-colors hover:bg-primary/8 hover:text-primary"
                            title="Add feature"
                          >
                            <Plus className="h-4 w-4" />
                          </button>
                        </td>
                      </tr>
                      {mod.expanded &&
                        mod.tasks.map((task, tIdx) => (
                          <Fragment key={task.id}>
                            <tr className="transition-colors hover:bg-primary/3">
                              <td className="text-center text-xs font-mono text-muted-foreground">
                                {offset + tIdx + 1}
                              </td>
                              <td className="pl-6 text-xs text-muted-foreground">
                                <div className="flex items-center gap-1.5">
                                  {mod.name}
                                  {task.complexity && (
                                    <span
                                      className={`${complexityBadge(
                                        task.complexity,
                                      )} hidden md:inline`}
                                    >
                                      {task.complexity.replace("_", " ")}
                                    </span>
                                  )}
                                </div>
                              </td>
                              <td>
                                <div className="flex items-center gap-1.5">
                                  {task.children?.length ? (
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        toggleTask(task.id);
                                      }}
                                      className="shrink-0 rounded p-0.5 hover:bg-muted/30"
                                    >
                                      {taskExpanded[task.id] ? (
                                        <ChevronDown className="h-3.5 w-3.5" />
                                      ) : (
                                        <ChevronRight className="h-3.5 w-3.5" />
                                      )}
                                    </button>
                                  ) : (
                                    <span className="w-3.5 shrink-0" />
                                  )}
                                  <EditableNameCell
                                    value={task.name}
                                    onChange={(v) => updateTaskName(mod.id, task.id, v)}
                                  />
                                </div>
                              </td>
                              <td className="text-center">
                                <EditableCell
                                  value={task.frontend}
                                  onChange={(v) =>
                                    updateTaskField(mod.id, task.id, "frontend", v)
                                  }
                                />
                              </td>
                              <td className="text-center">
                                <EditableCell
                                  value={task.backend}
                                  onChange={(v) =>
                                    updateTaskField(mod.id, task.id, "backend", v)
                                  }
                                />
                              </td>
                              <td className="text-center">
                                <EditableCell
                                  value={task.integration ?? 0}
                                  onChange={(v) =>
                                    updateTaskField(mod.id, task.id, "integration", v)
                                  }
                                />
                              </td>
                              <td className="text-center">
                                <EditableCell
                                  value={task.testing}
                                  onChange={(v) =>
                                    updateTaskField(mod.id, task.id, "testing", v)
                                  }
                                />
                              </td>
                              <td className="text-center text-sm font-semibold font-mono text-primary">
                                {fmtNum(task.total)}
                              </td>
                              <td className="text-center">
                                <div className="flex items-center justify-center gap-0.5">
                                  <button
                                    onClick={() => addSubFeature(mod.id, task.id)}
                                    className="rounded-lg p-1 text-primary/50 transition-all hover:bg-primary/8 hover:text-primary"
                                    title="Add sub-feature"
                                  >
                                    <Plus className="h-3.5 w-3.5" />
                                  </button>
                                  <button
                                    onClick={() => deleteTask(mod.id, task.id)}
                                    className="rounded-lg p-1 text-destructive/50 transition-all hover:bg-destructive/8 hover:text-destructive"
                                    title="Delete"
                                  >
                                    <Trash2 className="h-3.5 w-3.5" />
                                  </button>
                                </div>
                              </td>
                            </tr>
                            {taskExpanded[task.id] &&
                              task.children?.map((child) => (
                                <tr key={child.id} className="subtask-row">
                                  <td />
                                  <td />
                                  <td className="pl-10 text-sm">
                                    <div className="flex items-center gap-1.5">
                                      <span className="text-xs text-muted-foreground/40">
                                        ↳
                                      </span>
                                      <EditableNameCell
                                        value={child.name}
                                        onChange={(v) =>
                                          updateTaskName(mod.id, task.id, v, child.id)
                                        }
                                        className="text-sm"
                                      />
                                    </div>
                                  </td>
                                  <td className="text-center">
                                    <EditableCell
                                      value={child.frontend}
                                      onChange={(v) =>
                                        updateTaskField(
                                          mod.id,
                                          task.id,
                                          "frontend",
                                          v,
                                          child.id,
                                        )
                                      }
                                    />
                                  </td>
                                  <td className="text-center">
                                    <EditableCell
                                      value={child.backend}
                                      onChange={(v) =>
                                        updateTaskField(
                                          mod.id,
                                          task.id,
                                          "backend",
                                          v,
                                          child.id,
                                        )
                                      }
                                    />
                                  </td>
                                  <td className="text-center">
                                    <EditableCell
                                      value={child.integration ?? 0}
                                      onChange={(v) =>
                                        updateTaskField(
                                          mod.id,
                                          task.id,
                                          "integration",
                                          v,
                                          child.id,
                                        )
                                      }
                                    />
                                  </td>
                                  <td className="text-center">
                                    <EditableCell
                                      value={child.testing}
                                      onChange={(v) =>
                                        updateTaskField(
                                          mod.id,
                                          task.id,
                                          "testing",
                                          v,
                                          child.id,
                                        )
                                      }
                                    />
                                  </td>
                                  <td className="text-center text-sm font-medium font-mono text-primary">
                                    {fmtNum(child.total)}
                                  </td>
                                  <td className="text-center">
                                    <button
                                      onClick={() => deleteTask(mod.id, task.id, child.id)}
                                      className="rounded-lg p-1 text-destructive/50 hover:bg-destructive/8 hover:text-destructive"
                                    >
                                      <Trash2 className="h-3 w-3" />
                                    </button>
                                  </td>
                                </tr>
                              ))}
                          </Fragment>
                        ))}
                    </Fragment>
                  );
                })}
                <tr
                  className="font-bold"
                  style={{ background: "hsl(var(--muted) / 0.4)" }}
                >
                  <td />
                  <td colSpan={2} className="text-sm">
                    Grand Total
                  </td>
                  <td className="text-center text-sm font-mono text-primary">
                    {fmtNum(totalsByColumn.frontend)}
                  </td>
                  <td className="text-center text-sm font-mono text-primary">
                    {fmtNum(totalsByColumn.backend)}
                  </td>
                  <td className="text-center text-sm font-mono text-primary">
                    {fmtNum(totalsByColumn.integration)}
                  </td>
                  <td className="text-center text-sm font-mono text-primary">
                    {fmtNum(totalsByColumn.testing)}
                  </td>
                  <td className="text-center font-mono text-base font-bold text-primary">
                    {fmtNum(totalsByColumn.total)}
                  </td>
                  <td />
                </tr>
              </tbody>
            </table>
          </div>
          <div
            className="flex flex-wrap items-center justify-between gap-4 border-t border-border/30 px-5 py-4"
            style={{ background: "hsl(var(--muted) / 0.1)" }}
          >
            <div className="flex flex-wrap items-center gap-5 text-xs text-muted-foreground">
              {[
                { color: "bg-blue-500", label: "Frontend", val: totalsByColumn.frontend },
                { color: "bg-violet-500", label: "Backend", val: totalsByColumn.backend },
                {
                  color: "bg-amber-500",
                  label: "Integration",
                  val: totalsByColumn.integration,
                },
                { color: "bg-emerald-500", label: "Testing", val: totalsByColumn.testing },
              ].map((l) => (
                <span key={l.label} className="flex items-centered gap-2">
                  <span className={`h-2 w-2 rounded-full ${l.color}`} /> {l.label}{" "}
                  <strong className="font-mono text-foreground">{fmtNum(l.val)}</strong>
                </span>
              ))}
            </div>
            <div className="rounded-xl border border-primary/15 bg-primary/8 px-5 py-2.5 text-sm font-medium">
              Grand Total{" "}
              <strong className="ml-1.5 font-mono text-primary">
                {fmtNum(totalsByColumn.total)} hrs
              </strong>
            </div>
          </div>
        </div>
      ) : (
        <div className="card-spotlight rounded-2xl p-16 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-muted/30">
            <Search className="h-8 w-8 text-muted-foreground/40" />
          </div>
          <p className="font-medium text-muted-foreground">
            {searchQuery ? `No features match "${searchQuery}"` : "No features returned."}
          </p>
          {searchQuery && (
            <button
              onClick={() => onSearchChange("")}
              className="mt-3 text-sm font-semibold text-primary hover:underline"
            >
              Clear search
            </button>
          )}
        </div>
      )}

      {techStack.length > 0 && (
        <div>
          <div className="section-title">
            <h2>
              <Code2 className="mr-2 inline h-5 w-5 text-primary" />
              Recommended Tech Stack
            </h2>
            <span className="line" />
          </div>
          <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
            {techStack.map((t, i) => {
              const Icon = t.icon;
              return (
                <motion.div
                  key={t.category}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.07 }}
                  className="stat-bento shine-hover stat-blue group cursor-default p-5"
                >
                  <div className="stat-icon-wrap rounded-xl bg-primary/10 group-hover:bg-primary/15">
                    <Icon className="h-6 w-6 text-primary" />
                  </div>
                  <p className="mb-0.5 text-[10px] font-bold uppercase tracking-[0.1em] text-muted-foreground">
                    {t.category}
                  </p>
                  <p
                    className="mb-1.5 text-sm font-bold"
                    style={{ fontFamily: "'Sora', system-ui" }}
                  >
                    {t.tech}
                  </p>
                  <p className="text-xs leading-relaxed text-muted-foreground line-clamp-3">
                    {t.reason}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}

      {resources.length > 0 && (
        <div>
          <div className="section-title">
            <h2>
              <Users className="mr-2 inline h-5 w-5 text-primary" />
              Resource Allocation
            </h2>
            <span className="line" />
          </div>
          <div className="card-spotlight table-premium overflow-hidden rounded-2xl">
            <table className="estimation-table">
              <thead>
                <tr>
                  <th>Role</th>
                  <th className="text-center">Senior</th>
                  <th className="text-center">Mid</th>
                  <th className="text-center">Junior</th>
                  <th className="text-center font-bold text-primary">Total</th>
                </tr>
              </thead>
              <tbody>
                {resources.map((r) => (
                  <tr key={r.role}>
                    <td className="font-medium capitalize">
                      {r.role.replace(/_/g, " ")}
                    </td>
                    <td className="text-center font-mono">{fmtNum(r.senior)}</td>
                    <td className="text-center font-mono">{fmtNum(r.mid)}</td>
                    <td className="text-center font-mono">{fmtNum(r.junior)}</td>
                    <td className="text-center font-mono font-bold text-primary">
                      {fmtNum(r.total)}
                    </td>
                  </tr>
                ))}
                <tr
                  className="font-bold"
                  style={{ background: "hsl(var(--muted) / 0.4)" }}
                >
                  <td>Total Team</td>
                  <td className="text-center font-mono">
                    {fmtNum(resources.reduce((a, r) => a + r.senior, 0))}
                  </td>
                  <td className="text-center font-mono">
                    {fmtNum(resources.reduce((a, r) => a + r.mid, 0))}
                  </td>
                  <td className="text-center font-mono">
                    {fmtNum(resources.reduce((a, r) => a + r.junior, 0))}
                  </td>
                  <td className="text-center font-mono text-primary">
                    {fmtNum(resources.reduce((a, r) => a + r.total, 0))}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="cta-bar">
        <Button className="btn-primary-glow h-11 rounded-xl px-7 font-semibold">
          <CheckCircle className="relative z-10 mr-2 h-4 w-4" />{" "}
          <span className="relative z-10">Approve Estimation</span>
        </Button>
        <Button
          variant="outline"
          className="h-11 rounded-xl border-border/40 px-6 font-medium transition-all hover:border-primary/25 hover:bg-primary/5"
        >
          <Download className="mr-2 h-4 w-4" /> Download PDF
        </Button>
        <Button
          variant="outline"
          className="h-11 rounded-xl border-border/40 px-6 font-medium transition-all hover:border-accent/25 hover:bg-accent/5"
        >
          <Share2 className="mr-2 h-4 w-4" /> Share
        </Button>
      </div>
    </motion.div>
  );
}

