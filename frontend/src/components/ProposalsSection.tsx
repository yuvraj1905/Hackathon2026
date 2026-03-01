"use client";

import { useState } from "react";
import {
    FileText,
    Clock,
    Download,
    ExternalLink,
} from "lucide-react";
import Link from "next/link";
import { ProposalData, fmtNum } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { requestGoogleToken, uploadHtmlAsGoogleDoc } from "@/lib/googleDrive";

const API_BASE =
    (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_BASE) ||
    "http://localhost:8000";
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
    const [gdocLoading, setGdocLoading] = useState(false);
    const { toast } = useToast();

    const handleOpenInGoogleDocs = async ({ requestId }: { requestId: string }) => {
        if (!requestId) return;

        // Open a blank tab synchronously (in click context) to avoid popup blocker
        const newTab = window.open("about:blank", "_blank");

        setGdocLoading(true);
        try {
            // 1. Fetch rendered HTML from backend
            const res = await fetch(`${API_BASE}/proposal/html/${requestId}`);
            if (!res.ok) {
                const body = await res.json().catch(() => ({ detail: `Server error ${res.status}` }));
                throw new Error(body.detail || `Server error ${res.status}`);
            }
            const { html, title } = await res.json();

            // 2. Get OAuth token via Google Identity Services popup
            const token = await requestGoogleToken();

            // 3. Upload HTML as a Google Doc in the user's own Drive
            const docUrl = await uploadHtmlAsGoogleDoc(html, title, token);

            // 4. Navigate the pre-opened tab to the doc
            if (newTab) {
                newTab.location.href = docUrl;
            } else {
                window.open(docUrl, "_blank");
            }

            toast({
                title: "Google Doc created",
                description: "Proposal opened in your Google Drive.",
            });
        } catch (err: any) {
            // Close the blank tab on error
            newTab?.close();
            toast({
                title: "Google Docs export failed",
                description: err?.message || "Could not create Google Doc.",
                variant: "destructive",
            });
        } finally {
            setGdocLoading(false);
        }
    };

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

                    const requestId = p.request_id || "abc123";

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

                            {/* ── Action buttons ───────────────────────────────────────── */}
                            <div className="ml-auto flex shrink-0 items-center gap-2">
                                <Button
                                    size="sm"
                                    disabled={!requestId}
                                    onClick={() => window.open(`/proposal/pdf/${requestId}`, "_blank")}
                                    className="rounded-xl text-xs font-medium"
                                >
                                    <Download className="mr-1.5 h-3.5 w-3.5" />
                                    Download Proposal
                                </Button>

                                <Button
                                    size="sm"
                                    variant="outline"
                                    disabled={!requestId || gdocLoading}
                                    onClick={() => handleOpenInGoogleDocs({ requestId })}
                                    className="rounded-xl text-xs font-medium"
                                >
                                    {gdocLoading ? (
                                        <span className="mr-1.5 inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
                                    ) : (
                                        <ExternalLink className="mr-1.5 h-3.5 w-3.5" />
                                    )}
                                    {gdocLoading ? "Generating…" : "Open in Google Docs"}
                                </Button>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
