"use client";

import { Clock } from "lucide-react";
import { ProposalData } from "@/lib/utils";
import { fmtNum } from "@/lib/utils";

interface SummaryData {
  domain: string;
  platforms?: string[];
  totalHours: number;
  timeline: string;
  confidence: number;
}

interface EstimateSummaryPillsProps {
  summaryData: SummaryData;
  proposalData: ProposalData | null;
}

export function EstimateSummaryPills({ summaryData, proposalData }: EstimateSummaryPillsProps) {
  const show =
    summaryData.domain ||
    (summaryData.platforms && summaryData.platforms.length > 0) ||
    summaryData.timeline ||
    summaryData.confidence > 0 ||
    (proposalData && proposalData.minHours > 0);
  if (!show) return null;

  return (
    <div className="pill-group">
      {summaryData.domain && <span className="pill-primary capitalize">{summaryData.domain}</span>}
      {summaryData.platforms?.map((p) => (
        <span key={p} className="pill-muted capitalize">
          {p}
        </span>
      ))}
      {summaryData.timeline && (
        <span className="pill-muted">
          <Clock className="mr-1 h-3 w-3" />
          {summaryData.timeline}
        </span>
      )}
      {summaryData.confidence > 0 && <span className="pill-accent">{summaryData.confidence}% confidence</span>}
      {proposalData && proposalData.minHours > 0 && (
        <span className="pill-muted">
          {fmtNum(proposalData.minHours)}–{fmtNum(proposalData.maxHours)} hrs range
        </span>
      )}
    </div>
  );
}
