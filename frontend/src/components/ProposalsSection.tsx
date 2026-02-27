"use client";

import { FileText, Target, CheckCircle, ShieldAlert, AlertCircle, Clock } from "lucide-react";
import { ProposalData, fmtNum } from "@/lib/utils";

interface ProposalsSectionProps {
  proposalData: ProposalData | null;
  summaryData: { timeline: string; totalHours: number };
}

export function ProposalsSection({ proposalData, summaryData }: ProposalsSectionProps) {
  if (!proposalData) {
    return (
      <div className="card-spotlight rounded-2xl p-12 text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-muted/40">
          <FileText className="h-7 w-7 text-muted-foreground" />
        </div>
        <p className="text-sm text-muted-foreground">
          No proposals yet. Run an estimation in the{" "}
          <span className="font-semibold text-foreground">Estimates</span> tab to generate a
          proposal.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="section-title">
        <h2>
          <FileText className="mr-2 inline h-5 w-5 text-primary" />
          Latest Proposal
        </h2>
        <span className="line" />
      </div>

      {(proposalData.executiveSummary ||
        proposalData.deliverables.length > 0 ||
        proposalData.risks.length > 0) && (
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {proposalData.executiveSummary && (
              <div className="card-accent card-accent-primary md:col-span-2 lg:col-span-1 p-5">
                <div className="mb-3 flex items-center gap-2.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/12">
                    <FileText className="h-4 w-4 text-primary" />
                  </div>
                  <h3 className="text-sm font-bold">Executive Summary</h3>
                </div>
                <p className="text-xs leading-relaxed text-muted-foreground">
                  {proposalData.executiveSummary}
                </p>
              </div>
            )}

            {proposalData.deliverables.length > 0 && (
              <div className="card-accent card-accent-success p-5">
                <div className="mb-3 flex items-center gap-2.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/12">
                    <Target className="h-4 w-4 text-emerald-400" />
                  </div>
                  <h3 className="text-sm font-bold">Key Deliverables</h3>
                </div>
                <ul className="space-y-1.5">
                  {proposalData.deliverables.map((d, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 text-xs text-muted-foreground"
                    >
                      <CheckCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-400" />
                      {d}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {proposalData.risks.length > 0 && (
              <div className="card-accent card-accent-warning p-5">
                <div className="mb-3 flex items-center gap-2.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-500/12">
                    <ShieldAlert className="h-4 w-4 text-amber-400" />
                  </div>
                  <h3 className="text-sm font-bold">Risks</h3>
                </div>
                <ul className="space-y-1.5">
                  {proposalData.risks.map((r, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 text-xs text-muted-foreground"
                    >
                      <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-400" />
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

      {(summaryData.timeline || summaryData.totalHours || proposalData.minHours > 0) && (
        <div className="pill-group">
          {summaryData.timeline && (
            <span className="pill-muted">
              <Clock className="mr-1 h-3 w-3" />
              {summaryData.timeline}
            </span>
          )}
          {summaryData.totalHours > 0 && (
            <span className="pill-muted">
              Total {fmtNum(summaryData.totalHours)} hrs
            </span>
          )}
          {proposalData.minHours > 0 && (
            <span className="pill-accent">
              {fmtNum(proposalData.minHours)}–{fmtNum(proposalData.maxHours)} hrs range
            </span>
          )}
        </div>
      )}
    </div>
  );
}

