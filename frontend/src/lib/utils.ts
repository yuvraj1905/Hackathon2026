import type React from "react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { SubTask } from "@/types/dashboard";
import { FileText, Target, Layers, Code2, Clock, Sparkles } from "lucide-react";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const fmtNum = (n: number): string =>
  Number(n).toLocaleString(undefined, {
    maximumFractionDigits: 1,
    minimumFractionDigits: 0,
  });

export const calcTotal = (
  t: Pick<SubTask, "frontend" | "backend" | "integration" | "testing">,
) => t.frontend + t.backend + (t.integration ?? 0) + t.testing;

export function getPhaseRatios(phaseSplit: Record<string, number> | undefined) {
  if (!phaseSplit || typeof phaseSplit !== "object") return null;
  const f = Number(phaseSplit.frontend) || 0;
  const b = Number(phaseSplit.backend) || 0;
  const qa = Number(phaseSplit.qa) || 0;
  const total = f + b + qa;
  if (total <= 0) return null;
  return {
    frontend: f / total,
    backend: b / total,
    integration: 0,
    testing: qa / total,
  };
}

export function complexityBadge(c?: string) {
  if (!c) return "";
  const v = c.toLowerCase();
  if (v === "low") return "badge-simple";
  if (v === "high" || v === "very_high") return "badge-complex";
  return "badge-medium";
}

export interface TechRec {
  category: string;
  tech: string;
  reason: string;
  icon: React.ElementType;
}

export interface ResourceRow {
  role: string;
  senior: number;
  mid: number;
  junior: number;
  total: number;
}

export interface ProposalData {
  executiveSummary: string;
  scopeOfWork: string;
  deliverables: string[];
  risks: string[];
  assumptions: string[];
  minHours: number;
  maxHours: number;
}

export const PLATFORM_OPTIONS = [
  { value: "mobile", label: "Mobile" },
  { value: "web_app", label: "Web App" },
  { value: "design", label: "Design" },
  { value: "backend", label: "Backend" },
  { value: "admin", label: "Admin" },
] as const;

export const LOADING_STEPS = [
  { label: "Analyzing project description", icon: FileText, color: "text-blue-400" },
  { label: "Detecting domain & context", icon: Target, color: "text-violet-400" },
  { label: "Structuring features", icon: Layers, color: "text-cyan-400" },
  { label: "Recommending tech stack", icon: Code2, color: "text-emerald-400" },
  { label: "Estimating hours", icon: Clock, color: "text-amber-400" },
  { label: "Generating proposal", icon: Sparkles, color: "text-pink-400" },
] as const;



