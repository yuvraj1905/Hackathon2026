"use client";

import React, { Fragment } from "react";
import { ChevronDown, ChevronRight, Plus, Search, Trash2 } from "lucide-react";
import type { Module } from "@/types/dashboard";
import { complexityBadge, fmtNum } from "@/lib/utils";
import { EditableCell, EditableNameCell } from "./EditableEstimateCells";

interface TotalsByColumn {
  frontend: number;
  backend: number;
  integration: number;
  testing: number;
  total: number;
}

interface EstimateFeaturesTableProps {
  filteredModules: Module[];
  totalsByColumn: TotalsByColumn;
  searchQuery: string;
  taskExpanded: Record<string, boolean>;
  onSearchChange: (v: string) => void;
  toggleModule: (id: string) => void;
  toggleTask: (id: string) => void;
  updateTaskName: (moduleId: string, taskId: string, name: string, childId?: string) => void;
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
}

export function EstimateFeaturesTable({
  filteredModules,
  totalsByColumn,
  searchQuery,
  taskExpanded,
  onSearchChange,
  toggleModule,
  toggleTask,
  updateTaskName,
  updateTaskField,
  addTask,
  addSubFeature,
  deleteTask,
}: EstimateFeaturesTableProps) {
  if (filteredModules.length > 0) {
    return (
      <div className="card-spotlight table-premium overflow-hidden rounded-2xl">
        <div className="overflow-x-auto">
          <table className="estimation-table">
            <thead>
              <tr>
                <th className="w-10 text-center">#</th>
                <th className="min-w-[200px]">Feature</th>
                <th className="min-w-[200px]">Subfeature</th>
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
                const offset = filteredModules.slice(0, modIdx).reduce((a, m) => a + m.tasks.length, 0);
                return (
                  <Fragment key={`mod-${mod.id}`}>
                    <tr className="module-row cursor-pointer" onClick={() => toggleModule(mod.id)}>
                      <td className="text-center text-xs font-mono text-muted-foreground">{mod.id}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          {mod.expanded ? (
                            <ChevronDown className="h-4 w-4 shrink-0 text-primary/60" />
                          ) : (
                            <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
                          )}
                          <span className="font-bold">{mod.name}</span>
                        </div>
                      </td>
                      <td className="text-muted-foreground text-sm">
                        {mod.tasks.length} features
                      </td>
                      <td className="text-center text-sm font-medium font-mono">{fmtNum(mod.tasks.reduce((a, t) => a + t.frontend, 0))}</td>
                      <td className="text-center text-sm font-medium font-mono">{fmtNum(mod.tasks.reduce((a, t) => a + t.backend, 0))}</td>
                      <td className="text-center text-sm font-medium font-mono">{fmtNum(mod.tasks.reduce((a, t) => a + (t.integration ?? 0), 0))}</td>
                      <td className="text-center text-sm font-medium font-mono">{fmtNum(mod.tasks.reduce((a, t) => a + t.testing, 0))}</td>
                      <td className="text-center font-mono text-sm font-bold text-primary">{fmtNum(mod.tasks.reduce((a, t) => a + t.total, 0))}</td>
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
                            <td className="text-center text-xs font-mono text-muted-foreground">{offset + tIdx + 1}</td>
                            <td className="pl-6">
                              <div className="flex items-center gap-1.5">
                                {task.complexity && (
                                  <span className={`${complexityBadge(task.complexity)} hidden md:inline shrink-0`}>
                                    {task.complexity.replace("_", " ")}
                                  </span>
                                )}
                                <EditableNameCell value={task.name} onChange={(v) => updateTaskName(mod.id, task.id, v)} />
                              </div>
                            </td>
                            <td>
                              <div className="flex items-center gap-1.5">
                                {task.children?.length ? (
                                  <>
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
                                    <span className="text-muted-foreground text-sm">
                                      {task.children.length} subfeature{task.children.length !== 1 ? "s" : ""}
                                    </span>
                                  </>
                                ) : (
                                  <span className="text-muted-foreground/60">—</span>
                                )}
                              </div>
                            </td>
                            <td className="text-center">
                              <EditableCell value={task.frontend} onChange={(v) => updateTaskField(mod.id, task.id, "frontend", v)} />
                            </td>
                            <td className="text-center">
                              <EditableCell value={task.backend} onChange={(v) => updateTaskField(mod.id, task.id, "backend", v)} />
                            </td>
                            <td className="text-center">
                              <EditableCell value={task.integration ?? 0} onChange={(v) => updateTaskField(mod.id, task.id, "integration", v)} />
                            </td>
                            <td className="text-center">
                              <EditableCell value={task.testing} onChange={(v) => updateTaskField(mod.id, task.id, "testing", v)} />
                            </td>
                            <td className="text-center text-sm font-semibold font-mono text-primary">{fmtNum(task.total)}</td>
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
                                <td className="pl-8 text-muted-foreground text-sm" />
                                <td className="pl-10 text-sm">
                                  <div className="flex items-center gap-1.5">
                                    <span className="text-xs text-muted-foreground/40">↳</span>
                                    <EditableNameCell
                                      value={child.name}
                                      onChange={(v) => updateTaskName(mod.id, task.id, v, child.id)}
                                      className="text-sm"
                                    />
                                  </div>
                                </td>
                                <td className="text-center">
                                  <EditableCell
                                    value={child.frontend}
                                    onChange={(v) => updateTaskField(mod.id, task.id, "frontend", v, child.id)}
                                  />
                                </td>
                                <td className="text-center">
                                  <EditableCell
                                    value={child.backend}
                                    onChange={(v) => updateTaskField(mod.id, task.id, "backend", v, child.id)}
                                  />
                                </td>
                                <td className="text-center">
                                  <EditableCell
                                    value={child.integration ?? 0}
                                    onChange={(v) => updateTaskField(mod.id, task.id, "integration", v, child.id)}
                                  />
                                </td>
                                <td className="text-center">
                                  <EditableCell
                                    value={child.testing}
                                    onChange={(v) => updateTaskField(mod.id, task.id, "testing", v, child.id)}
                                  />
                                </td>
                                <td className="text-center text-sm font-medium font-mono text-primary">{fmtNum(child.total)}</td>
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
              <tr className="font-bold" style={{ background: "hsl(var(--muted) / 0.4)" }}>
                <td />
                <td colSpan={2} className="text-sm">
                  Grand Total
                </td>
                <td className="text-center text-sm font-mono text-primary">{fmtNum(totalsByColumn.frontend)}</td>
                <td className="text-center text-sm font-mono text-primary">{fmtNum(totalsByColumn.backend)}</td>
                <td className="text-center text-sm font-mono text-primary">{fmtNum(totalsByColumn.integration)}</td>
                <td className="text-center text-sm font-mono text-primary">{fmtNum(totalsByColumn.testing)}</td>
                <td className="text-center font-mono text-base font-bold text-primary">{fmtNum(totalsByColumn.total)}</td>
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
              { color: "bg-amber-500", label: "Integration", val: totalsByColumn.integration },
              { color: "bg-emerald-500", label: "Testing", val: totalsByColumn.testing },
            ].map((l) => (
              <span key={l.label} className="flex items-centered gap-2">
                <span className={`h-2 w-2 rounded-full ${l.color}`} /> {l.label}{" "}
                <strong className="font-mono text-foreground">{fmtNum(l.val)}</strong>
              </span>
            ))}
          </div>
          <div className="rounded-xl border border-primary/15 bg-primary/8 px-5 py-2.5 text-sm font-medium">
            Grand Total <strong className="ml-1.5 font-mono text-primary">{fmtNum(totalsByColumn.total)} hrs</strong>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card-spotlight rounded-2xl p-16 text-center">
      <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-muted/30">
        <Search className="h-8 w-8 text-muted-foreground/40" />
      </div>
      <p className="font-medium text-muted-foreground">
        {searchQuery ? `No features match "${searchQuery}"` : "No features returned."}
      </p>
      {searchQuery && (
        <button onClick={() => onSearchChange("")} className="mt-3 text-sm font-semibold text-primary hover:underline">
          Clear search
        </button>
      )}
    </div>
  );
}
