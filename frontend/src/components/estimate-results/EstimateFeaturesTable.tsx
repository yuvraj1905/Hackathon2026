"use client";

import { Fragment } from "react";
import { ChevronDown, ChevronRight, Plus, Search, Trash2 } from "lucide-react";
import type { Module } from "@/types/dashboard";
import { complexityBadge, fmtInt } from "@/lib/utils";
import { EditableNameCell } from "./EditableEstimateCells";

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
  addTask,
  addSubFeature,
  deleteTask,
}: EstimateFeaturesTableProps) {
  if (filteredModules.length > 0) {
    return (
      <div className="card-spotlight table-premium overflow-hidden rounded-2xl border border-border/40 shadow-lg shadow-black/5">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[520px] table-fixed text-left text-sm">
            <colgroup>
              <col className="w-9" />
              <col style={{ width: "36%" }} />
              <col className="w-24" />
              <col className="w-28" />
              <col className="w-20" />
              <col className="w-20" />
            </colgroup>
            <thead>
              <tr className="border-b border-border/50 bg-muted/20">
                <th className="py-2 pl-2 pr-1 text-center font-semibold text-muted-foreground">#</th>
                <th className="py-2 pl-2 pr-2 font-semibold">Feature</th>
                <th className="py-2 px-1.5 font-semibold text-muted-foreground">Complexity</th>
                <th className="py-2 px-1.5 text-muted-foreground">Subfeatures</th>
                <th className="py-2 px-1.5 text-right font-semibold text-primary">Development Hours</th>
                <th className="py-2 pl-1.5 pr-2 text-center font-semibold text-muted-foreground">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredModules.map((mod, modIdx) => {
                const offset = filteredModules.slice(0, modIdx).reduce((a, m) => a + m.tasks.length, 0);
                return (
                  <Fragment key={`mod-${mod.id}`}>
                    <tr
                      className="cursor-pointer border-b border-border/30 bg-muted/10 transition-colors hover:bg-muted/20"
                      onClick={() => toggleModule(mod.id)}
                    >
                      <td className="py-2 pl-2 pr-1 text-center text-xs font-mono text-muted-foreground" />
                      <td className="py-2 pl-2 pr-2">
                        <div className="flex min-w-0 items-center gap-1.5">
                          {mod.expanded ? (
                            <ChevronDown className="h-4 w-4 shrink-0 text-primary/70" />
                          ) : (
                            <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
                          )}
                          <span className="truncate font-semibold tracking-tight">{mod.name}</span>
                        </div>
                      </td>
                      <td className="py-2 px-1.5 text-muted-foreground/70">—</td>
                      <td className="py-2 px-1.5 text-muted-foreground">
                        {mod.tasks.length} feature{mod.tasks.length !== 1 ? "s" : ""}
                      </td>
                      <td className="py-2 px-1.5 text-right font-mono font-semibold tabular-nums text-primary">
                        {fmtInt(mod.tasks.reduce((a, t) => a + t.total, 0))}
                      </td>
                      <td className="py-2 pl-1.5 pr-2 text-center">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            addTask(mod.id);
                          }}
                          className="rounded-lg p-1.5 text-primary/70 transition-colors hover:bg-primary/15 hover:text-primary text-sm"
                          title="Add feature"
                        >
                          <Plus className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                    {mod.expanded &&
                      mod.tasks.map((task, tIdx) => (
                        <Fragment key={task.id}>
                          <tr className="border-b border-border/20 transition-colors hover:bg-background/50 align-top">
                            <td className="py-2 pl-2 pr-1 align-top text-center text-xs font-mono text-muted-foreground">
                              {offset + tIdx + 1}
                            </td>
                            <td className="py-2 pl-3 pr-2 align-top">
                              <div className="min-w-0">
                                <EditableNameCell value={task.name} onChange={(v) => updateTaskName(mod.id, task.id, v)} />
                              </div>
                            </td>
                            <td className="py-2 px-1.5 align-top">
                              {task.complexity ? (
                                <span className={`${complexityBadge(task.complexity)} inline-block`}>
                                  {String(task.complexity).replace("_", " ")}
                                </span>
                              ) : (
                                <span className="text-muted-foreground/60">—</span>
                              )}
                            </td>
                            <td className="py-2 px-1.5 align-top">
                              {(task.children?.length ?? 0) > 0 ? (
                                <div className="min-w-0">
                                  <button
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      toggleTask(task.id);
                                    }}
                                    className="flex items-center gap-1 rounded p-0.5 hover:bg-muted/40 text-left w-full"
                                  >
                                    {taskExpanded[task.id] ? (
                                      <ChevronDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                                    ) : (
                                      <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                                    )}
                                    <span className="text-muted-foreground text-sm">
                                      {task.children!.length} Sub-features
                                    </span>
                                  </button>
                                </div>
                              ) : (
                                <span className="text-muted-foreground/70 text-sm">0 Sub-features</span>
                              )}
                            </td>
                            <td className="py-2 px-1.5 align-top text-right font-mono font-medium tabular-nums text-primary">
                              {fmtInt(task.total)}
                            </td>
                            <td className="py-2 pl-1.5 pr-2 align-top">
                              <div className="flex items-center justify-center gap-0.5">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    addSubFeature(mod.id, task.id);
                                  }}
                                  className="rounded-lg p-1.5 text-primary/60 transition-colors hover:bg-primary/15 hover:text-primary"
                                  title="Add sub-feature"
                                >
                                  <Plus className="h-3.5 w-3.5" />
                                </button>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    deleteTask(mod.id, task.id);
                                  }}
                                  className="rounded-lg p-1.5 text-destructive/60 transition-colors hover:bg-destructive/15 hover:text-destructive"
                                  title="Delete"
                                >
                                  <Trash2 className="h-3.5 w-3.5" />
                                </button>
                              </div>
                            </td>
                          </tr>
                          {taskExpanded[task.id] &&
                            task.children?.map((child) => (
                              <tr key={child.id} className="border-b border-border/10 bg-muted/5">
                                <td className="py-1.5 pl-2 pr-1" />
                                <td className="py-1.5 pl-3 pr-2" />
                                <td className="py-1.5 px-1.5" />
                                <td className="py-1.5 pl-3 pr-2 align-top">
                                  <div className="flex min-w-0 items-start gap-1.5">
                                    <span className="shrink-0 text-muted-foreground/60">–</span>
                                    <EditableNameCell
                                      value={child.name}
                                      onChange={(v) => updateTaskName(mod.id, task.id, v, child.id)}
                                      className="min-w-0 text-sm text-muted-foreground break-words whitespace-normal leading-snug"
                                    />
                                  </div>
                                </td>
                                <td className="py-1.5 px-1.5 text-right font-mono text-sm tabular-nums text-primary">
                                  {fmtInt(child.total)}
                                </td>
                                <td className="py-1.5 pl-1.5 pr-2 text-center">
                                  <button
                                    onClick={() => deleteTask(mod.id, task.id, child.id)}
                                    className="rounded p-1.5 text-destructive/60 transition-colors hover:bg-destructive/15 hover:text-destructive"
                                    title="Delete subfeature"
                                  >
                                    <Trash2 className="h-3.5 w-3.5" />
                                  </button>
                                </td>
                              </tr>
                            ))}
                        </Fragment>
                      ))}
                  </Fragment>
                );
              })}
              <tr className="border-t-2 border-primary/20 bg-primary/5 font-semibold">
                <td className="py-2.5 pl-2 pr-1" />
                <td colSpan={3} className="py-2.5 pl-2 pr-2">
                  Grand Total
                </td>
                <td className="py-2.5 px-1.5 text-right font-mono text-base tabular-nums text-primary">
                  {fmtInt(totalsByColumn.total)}
                </td>
                <td className="py-2.5 pl-1.5 pr-2" />
              </tr>
            </tbody>
          </table>
        </div>
        <div className="flex flex-wrap items-center justify-end border-t border-border/30 bg-muted/10 px-4 py-3">
          <div className="rounded-lg border border-primary/20 bg-primary/10 px-4 py-2 text-sm font-medium">
            Total effort <strong className="ml-1 font-mono text-primary">{fmtInt(totalsByColumn.total)} hrs</strong>
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
