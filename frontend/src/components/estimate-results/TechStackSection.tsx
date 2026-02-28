"use client";

import { motion } from "framer-motion";
import { Cloud, Code2, Database, Monitor, Server, Zap } from "lucide-react";
import type { TechRec } from "@/lib/utils";

interface TechStackSectionProps {
  techStackStructured: Record<string, unknown> | null | undefined;
  techStack: TechRec[];
}

export function TechStackSection({ techStackStructured, techStack }: TechStackSectionProps) {
  const hasStructured = techStackStructured && typeof techStackStructured === "object";
  const hasFallback = techStack.length > 0;
  if (!hasStructured && !hasFallback) return null;

  return (
    <div>
      <div className="section-title">
        <h2>
          <Code2 className="mr-2 inline h-5 w-5 text-primary" />
          Recommended Tech Stack
        </h2>
        <span className="line" />
      </div>

      {hasStructured ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {/* Frontend by platform */}
          {Boolean(techStackStructured!.frontend && typeof techStackStructured!.frontend === "object" && !Array.isArray(techStackStructured!.frontend)) &&
            Object.entries(techStackStructured!.frontend as Record<string, Record<string, unknown>>).map(([platform, config]) => {
              if (!config || typeof config !== "object") return null;
              const skip = new Set(["justification", "type", "recommended"]);
              const label = platform.charAt(0).toUpperCase() + platform.slice(1).toLowerCase();
              return (
                <motion.div
                  key={platform}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="card-spotlight rounded-2xl p-5 border border-border/30"
                >
                  <h3 className="text-sm font-bold text-primary mb-2 flex items-center gap-2">
                    <Monitor className="h-4 w-4" />
                    Frontend ({label})
                  </h3>
                  <dl className="space-y-1">
                    {Object.entries(config)
                      .filter(([k]) => !skip.has(k) && config[k] != null && String(config[k]).trim() !== "")
                      .map(([k, v]) => (
                        <div key={k} className="flex justify-between gap-2 text-xs py-0.5">
                          <dt className="text-muted-foreground capitalize shrink-0">{k.replace(/_/g, " ")}:</dt>
                          <dd className="font-medium text-right min-w-0 truncate" title={typeof v === "string" ? v : String(v)}>
                            {typeof v === "string" ? v : String(v)}
                          </dd>
                        </div>
                      ))}
                  </dl>
                </motion.div>
              );
            })}

          {Boolean(techStackStructured!.backend && typeof techStackStructured!.backend === "object" && !Array.isArray(techStackStructured!.backend)) && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="card-spotlight rounded-2xl p-5 border border-border/30">
              <h3 className="text-sm font-bold text-primary mb-2 flex items-center gap-2">
                <Server className="h-4 w-4" />
                Backend
              </h3>
              <dl className="space-y-1">
                {Object.entries(techStackStructured!.backend as Record<string, unknown>)
                  .filter(
                    ([k]) =>
                      !["justification", "type", "recommended"].includes(k) &&
                      (techStackStructured!.backend as Record<string, unknown>)[k] != null &&
                      (techStackStructured!.backend as Record<string, unknown>)[k] !== "",
                  )
                  .map(([k, v]) => (
                    <div key={k} className="flex justify-between gap-2 text-xs py-0.5">
                      <dt className="text-muted-foreground capitalize shrink-0">{k.replace(/_/g, " ")}:</dt>
                      <dd className="font-medium text-right min-w-0 truncate" title={typeof v === "string" ? v : String(v)}>
                        {typeof v === "string" ? v : String(v)}
                      </dd>
                    </div>
                  ))}
              </dl>
            </motion.div>
          )}

          {/* Database */}
          {Boolean(techStackStructured!.database && typeof techStackStructured!.database === "object" && !Array.isArray(techStackStructured!.database)) && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="card-spotlight rounded-2xl p-5 border border-border/30">
              <h3 className="text-sm font-bold text-primary mb-2 flex items-center gap-2">
                <Database className="h-4 w-4" />
                Database
              </h3>
              <dl className="space-y-1">
                {["primary", "secondary", "cache", "search"].map((key) => {
                  const entry = (techStackStructured!.database as Record<string, unknown>)[key];
                  if (!entry || typeof entry !== "object" || !("name" in entry)) return null;
                  const name = (entry as { name?: string }).name;
                  const useCase = (entry as { use_case?: string }).use_case;
                  const label = key.charAt(0).toUpperCase() + key.slice(1);
                  const val = [name ?? "", useCase].filter(Boolean).join(" — ");
                  return (
                    <div key={key} className="flex justify-between gap-2 text-xs py-0.5">
                      <dt className="text-muted-foreground capitalize shrink-0">{label}:</dt>
                      <dd className="font-medium text-right min-w-0 truncate" title={val}>
                        {val}
                      </dd>
                    </div>
                  );
                })}
              </dl>
            </motion.div>
          )}

          {/* Infrastructure */}
          {Boolean(techStackStructured!.infrastructure && typeof techStackStructured!.infrastructure === "object" && !Array.isArray(techStackStructured!.infrastructure)) && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="card-spotlight rounded-2xl p-5 border border-border/30">
              <h3 className="text-sm font-bold text-primary mb-2 flex items-center gap-2">
                <Cloud className="h-4 w-4" />
                Infrastructure
              </h3>
              <dl className="space-y-1">
                {Object.entries(techStackStructured!.infrastructure as Record<string, unknown>)
                  .filter(([k]) => !["recommendations", "mobile_deployment"].includes(k))
                  .map(([key, entry]) => {
                    if (!entry || typeof entry !== "object") return null;
                    const name = (entry as { name?: string }).name;
                    const useCase = (entry as { use_case?: string }).use_case;
                    const label = key.replace(/_/g, " ");
                    const val = [name || String(entry), useCase].filter(Boolean).join(" — ");
                    return (
                      <div key={key} className="flex justify-between gap-2 text-xs py-0.5">
                        <dt className="text-muted-foreground capitalize shrink-0">{label}:</dt>
                        <dd className="font-medium text-right min-w-0 truncate" title={val}>
                          {val}
                        </dd>
                      </div>
                    );
                  })}
              </dl>
            </motion.div>
          )}

          {/* Third-party services */}
          {Boolean(
            techStackStructured!.third_party_services &&
            typeof techStackStructured!.third_party_services === "object" &&
            !Array.isArray(techStackStructured!.third_party_services),
          ) && (
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                className="card-spotlight rounded-2xl p-5 border border-border/30 sm:col-span-2 lg:col-span-1"
              >
                <h3 className="text-sm font-bold text-primary mb-2 flex items-center gap-2">
                  <Zap className="h-4 w-4" />
                  Third-party services
                </h3>
                <div className="space-y-2">
                  {Object.entries(
                    techStackStructured!.third_party_services as Record<string, { services?: Array<{ name?: string; justification?: string }> }>,
                  ).map(([category, data]) => {
                    const services = data?.services;
                    if (!Array.isArray(services) || services.length === 0) return null;
                    const catLabel = category.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
                    return (
                      <div key={category}>
                        <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-0.5">{catLabel}</p>
                        <ul className="space-y-0.5">
                          {services.map((s, i) => (
                            <li key={i} className="text-xs flex justify-between gap-2 py-0.5 min-w-0">
                              <span className="font-medium shrink-0">{s.name ?? "—"}</span>
                              {s.justification && (
                                <span className="text-muted-foreground text-[11px] min-w-0 truncate" title={s.justification}>
                                  {s.justification}
                                </span>
                              )}
                            </li>
                          ))}
                        </ul>
                      </div>
                    );
                  })}
                </div>
              </motion.div>
            )}
        </div>
      ) : (
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
                <p className="mb-0.5 text-[10px] font-bold uppercase tracking-[0.1em] text-muted-foreground">{t.category}</p>
                <p className="mb-1.5 text-sm font-bold" style={{ fontFamily: "'Sora', system-ui" }}>
                  {t.tech}
                </p>
                <p className="text-xs leading-relaxed text-muted-foreground line-clamp-3">{t.reason}</p>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
