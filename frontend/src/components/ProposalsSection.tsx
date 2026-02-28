"use client";

import Link from "next/link";
import {
    FileText,
    Target,
    CheckCircle,
    ShieldAlert,
    AlertCircle,
    Clock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProposalData, fmtNum } from "@/lib/utils";
import type { StoredProposalSummary } from "@/lib/estimateApi";

interface ProposalsSectionProps {
    proposalData: ProposalData | null;
    summaryData: { timeline: string; totalHours: number };
    proposals: StoredProposalSummary[];
}

export function ProposalsSection({
    proposalData,
    summaryData,
    proposals,
}: ProposalsSectionProps) {
    if (!proposals.length) {
        return (
            <div className="card-spotlight rounded-2xl p-12 text-center flex flex-col items-center justify-center gap-4">
                <div className="mx-auto mb-2 flex h-14 w-14 items-center justify-center rounded-2xl bg-muted/40">
                    <FileText className="h-7 w-7 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground max-w-md">
                    No proposals yet. Start by generating a new proposal from
                    your project idea.
                </p>
                <Link href="/proposals/new">
                    <Button size="lg" className="btn-primary-glow mt-2">
                        Generate new proposal
                    </Button>
                </Link>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="section-title">
                <h2>
                    <FileText className="mr-2 inline h-5 w-5 text-primary" />
                    Proposals
                </h2>
                <Link href="/proposals/new">
                    <Button size="sm" className="btn-primary-glow shrink-0">
                        Generate Proposal
                    </Button>
                </Link>
                <span className="line" />
            </div>

            <div className="space-y-3">
                {proposals.map((p) => {
                    const created = new Date(p.createdAt);
                    const createdLabel = created.toLocaleDateString(undefined, {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                    });

                    return (
                        <div
                            key={p.id}
                            className="glass-card-hover p-5 flex items-center justify-between"
                        >
                            <div className="flex items-center gap-4">
                                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                                    <FileText className="w-5 h-5 text-primary" />
                                </div>
                                <div>
                                    <p className="font-medium">{p.title}</p>
                                    <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                                        {p.domain && (
                                            <span className="px-2 py-0.5 rounded-full bg-muted/60">
                                                {p.domain}
                                            </span>
                                        )}
                                        <span className="flex items-center gap-1">
                                            <Clock className="w-3 h-3" />
                                            {createdLabel}
                                        </span>
                                        {p.totalHours > 0 && (
                                            <span>
                                                {fmtNum(p.totalHours)} hrs
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>

                            <Link href="/proposals/new">
                                <Button variant="outline" size="sm" className="shrink-0">
                                    Generate Proposal
                                </Button>
                            </Link>
                        </div>
                    );
                })}
            </div>

            {proposalData && (
                <>
                    <div className="section-title mt-8">
                        <h2>
                            <FileText className="mr-2 inline h-5 w-5 text-primary" />
                            Latest Proposal Details
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
                                        <h3 className="text-sm font-bold">
                                            Executive Summary
                                        </h3>
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
                                        <h3 className="text-sm font-bold">
                                            Key Deliverables
                                        </h3>
                                    </div>
                                    <ul className="space-y-1.5">
                                        {proposalData.deliverables.map(
                                            (d, i) => (
                                                <li
                                                    key={i}
                                                    className="flex items-start gap-2 text-xs text-muted-foreground"
                                                >
                                                    <CheckCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-400" />
                                                    {d}
                                                </li>
                                            ),
                                        )}
                                    </ul>
                                </div>
                            )}

                            {proposalData.risks.length > 0 && (
                                <div className="card-accent card-accent-warning p-5">
                                    <div className="mb-3 flex items-center gap-2.5">
                                        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-500/12">
                                            <ShieldAlert className="h-4 w-4 text-amber-400" />
                                        </div>
                                        <h3 className="text-sm font-bold">
                                            Risks
                                        </h3>
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

                    {(summaryData.timeline ||
                        summaryData.totalHours ||
                        proposalData.minHours > 0) && (
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
                                    {fmtNum(proposalData.minHours)}–
                                    {fmtNum(proposalData.maxHours)} hrs
                                </span>
                            )}
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
