import { Cloud, Database, Monitor, Server, Zap } from "lucide-react";
import type { Module, SubTask } from "@/types/dashboard";
import {
  getPhaseRatios,
  type ProposalData,
  type ResourceRow,
  type TechRec,
} from "@/lib/utils";

function isTechStackAgentFormat(d: any): boolean {
  if (!d || typeof d !== "object") return false;
  const f = d.frontend;
  return (
    f !== null &&
    typeof f === "object" &&
    !Array.isArray(f) &&
    (d.backend == null || typeof d.backend === "object")
  );
}

type TechStackIcons = {
  Monitor: typeof Monitor;
  Server: typeof Server;
  Database: typeof Database;
  Cloud: typeof Cloud;
  Zap: typeof Zap;
};

function getName(obj: unknown): string | null {
  if (
    obj &&
    typeof obj === "object" &&
    "name" in obj &&
    typeof (obj as { name: unknown }).name === "string"
  ) {
    return (obj as { name: string }).name;
  }
  return null;
}

function normalizeTechStackFromAgent(
  data: any,
  icons: TechStackIcons,
): TechRec[] {
  const d = data || {};
  const justification = (d.justification ?? "").toString();
  const recs: TechRec[] = [];

  // Frontend (per-platform)
  if (
    d.frontend &&
    typeof d.frontend === "object" &&
    !Array.isArray(d.frontend)
  ) {
    const parts: string[] = [];
    for (const [platform, config] of Object.entries(d.frontend)) {
      if (!config || typeof config !== "object") continue;
      const c = config as Record<string, string>;
      const vals = [
        c.framework,
        c.language,
        c.styling,
        c.ui_library,
        c.state_management,
        c.navigation,
        c.build_service,
      ].filter(Boolean);
      if (vals.length) {
        const label =
          String(platform).charAt(0).toUpperCase() + String(platform).slice(1);
        parts.push(`${label}: ${vals.join(", ")}`);
      }
    }
    if (parts.length) {
      recs.push({
        category: "Frontend",
        tech: parts.join(". "),
        reason: justification,
        icon: icons.Monitor,
      });
    }
  }

  // Backend
  if (d.backend && typeof d.backend === "object" && !Array.isArray(d.backend)) {
    const skip = new Set(["justification", "type"]);
    const back = d.backend as Record<string, unknown>;
    const vals = Object.entries(back)
      .filter(([k]) => !skip.has(k) && back[k] != null && back[k] !== "")
      .map(([, v]) => String(v));
    if (vals.length) {
      recs.push({
        category: "Backend",
        tech: vals.join(", "),
        reason: justification,
        icon: icons.Server,
      });
    }
  }

  // Database
  if (
    d.database &&
    typeof d.database === "object" &&
    !Array.isArray(d.database)
  ) {
    const names: string[] = [];
    for (const key of ["primary", "secondary", "cache", "search"]) {
      const n = getName((d.database as Record<string, unknown>)[key]);
      if (n) names.push(n);
    }
    if (names.length) {
      recs.push({
        category: "Database",
        tech: names.join(", "),
        reason: justification,
        icon: icons.Database,
      });
    }
  }

  // Infrastructure
  if (
    d.infrastructure &&
    typeof d.infrastructure === "object" &&
    !Array.isArray(d.infrastructure)
  ) {
    const names: string[] = [];
    const inf = d.infrastructure as Record<string, unknown>;
    for (const key of [
      "cloud_provider",
      "containerization",
      "orchestration",
      "reverse_proxy",
      "frontend_hosting",
    ]) {
      const n = getName(inf[key]);
      if (n) names.push(n);
    }
    const buildName = getName(
      inf.mobile_deployment && typeof inf.mobile_deployment === "object"
        ? (inf.mobile_deployment as Record<string, unknown>).build_service
        : null,
    );
    if (buildName) names.push(buildName);
    if (names.length) {
      recs.push({
        category: "Infrastructure",
        tech: names.join(", "),
        reason: justification,
        icon: icons.Cloud,
      });
    }
  }

  // Third-party services
  if (
    d.third_party_services &&
    typeof d.third_party_services === "object" &&
    !Array.isArray(d.third_party_services)
  ) {
    const names: string[] = [];
    for (const cat of Object.values(d.third_party_services)) {
      if (!cat || typeof cat !== "object") continue;
      const svcs = (cat as Record<string, unknown>).services;
      if (Array.isArray(svcs)) {
        for (const s of svcs) {
          const n = getName(s);
          if (n) names.push(n);
        }
      }
    }
    if (names.length) {
      recs.push({
        category: "Services",
        tech: names.join(", "),
        reason: justification,
        icon: icons.Zap,
      });
    }
  }

  return recs;
}

function buildTechStackRecs(techStackData: any): TechRec[] {
  const justification = (techStackData.justification ?? "").toString();
  const icons = { Monitor, Server, Database, Cloud, Zap };
  if (isTechStackAgentFormat(techStackData)) {
    return normalizeTechStackFromAgent(techStackData, icons);
  }
  return [
    ...(Array.isArray(techStackData.frontend) && techStackData.frontend.length
      ? [
          {
            category: "Frontend",
            tech: techStackData.frontend.join(", "),
            reason: justification,
            icon: Monitor,
          },
        ]
      : []),
    ...(Array.isArray(techStackData.backend) && techStackData.backend.length
      ? [
          {
            category: "Backend",
            tech: techStackData.backend.join(", "),
            reason: justification,
            icon: Server,
          },
        ]
      : []),
    ...(Array.isArray(techStackData.database) && techStackData.database.length
      ? [
          {
            category: "Database",
            tech: techStackData.database.join(", "),
            reason: justification,
            icon: Database,
          },
        ]
      : []),
    ...(Array.isArray(techStackData.infrastructure) &&
    techStackData.infrastructure.length
      ? [
          {
            category: "Infrastructure",
            tech: techStackData.infrastructure.join(", "),
            reason: justification,
            icon: Cloud,
          },
        ]
      : []),
    ...(Array.isArray(techStackData.third_party_services) &&
    techStackData.third_party_services.length
      ? [
          {
            category: "Services",
            tech: techStackData.third_party_services.join(", "),
            reason: justification,
            icon: Zap,
          },
        ]
      : []),
  ];
}

export interface TransformEstimateResult {
  modules: Module[];
  techStack: TechRec[];
  techStackStructured: Record<string, unknown> | null;
  resources: ResourceRow[];
  summary: {
    domain: string;
    platforms: string[];
    totalHours: number;
    timeline: string;
    confidence: number;
  };
  proposal: ProposalData;
}

export function transformEstimateResponse(data: any): TransformEstimateResult {
  const estimation = data.estimation || {};
  const features: any[] = estimation.features || [];
  const techStackData = data.tech_stack || {};
  const planning = data.planning || {};
  const domainDetection = data.domain_detection || {};
  const proposalRaw = data.proposal || {};

  const ratios = getPhaseRatios(planning.phase_split) ?? {
    frontend: 0.4,
    backend: 0.35,
    integration: 0,
    testing: 0.15,
  };

  const tasks: SubTask[] = features.map((f: any, i: number) => {
    const hours = Number(f.estimated_hours) || 0;
    const fe = Math.round(hours * ratios.frontend);
    const be = Math.round(hours * ratios.backend);
    const test = Math.round(hours * ratios.testing);
    const integ = Math.max(0, hours - fe - be - test);
    return {
      id: String(i + 1),
      name:
        (f.name || f.description || "").trim() || `Feature ${i + 1}`,
      frontend: fe,
      backend: be,
      integration: integ,
      testing: test,
      total: hours,
      complexity: f.complexity,
    };
  });

  const domainStr = (domainDetection.detected_domain ?? "")
    .toString()
    .replace(/_/g, " ")
    .trim();
  const moduleName = domainStr
    ? domainStr.charAt(0).toUpperCase() + domainStr.slice(1)
    : "Project";
  const modules: Module[] = [
    { id: "1", name: moduleName, expanded: true, tasks },
  ];

  const techStack = buildTechStackRecs(techStackData);

  // Platforms from frontend keys only (web, admin, mobile) – show what build types exist
  const frontendKeys = Object.keys(techStackData.frontend || {});
  const platforms = frontendKeys.map((p) =>
    p.charAt(0).toUpperCase() + p.slice(1).toLowerCase(),
  );

  const teamRec: Record<string, unknown> =
    planning.team_recommendation || proposalRaw.team_composition || {};
  const resources: ResourceRow[] = Object.entries(teamRec).map(
    ([role, count]) => {
      const n = Number(count) || 0;
      return { role, senior: 0, mid: n, junior: 0, total: n };
    },
  );

  const totalHours = Number(estimation.total_hours) || 0;
  const timelineWeeks = proposalRaw.timeline_weeks ?? planning.timeline_weeks;
  const summary = {
    domain: domainStr,
    platforms,
    totalHours,
    timeline: timelineWeeks != null ? `${timelineWeeks} weeks` : "",
    confidence: Math.round(
      Number(
        estimation.confidence_score || domainDetection.confidence || 0,
      ) * 100,
    ),
  };

  const proposal: ProposalData = {
    executiveSummary: proposalRaw.executive_summary || "",
    scopeOfWork: proposalRaw.scope_of_work || "",
    deliverables: Array.isArray(proposalRaw.deliverables)
      ? proposalRaw.deliverables
      : [],
    risks: Array.isArray(proposalRaw.risks) ? proposalRaw.risks : [],
    assumptions: Array.isArray(estimation.assumptions)
      ? estimation.assumptions
      : [],
    minHours: Number(estimation.min_hours) || 0,
    maxHours: Number(estimation.max_hours) || 0,
  };

  return {
    modules,
    techStack,
    techStackStructured: techStackData && typeof techStackData === "object" ? (techStackData as Record<string, unknown>) : null,
    resources,
    summary,
    proposal,
  };
}
