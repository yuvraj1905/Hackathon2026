"use client";

import { useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Brain } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    EstimateInputSection,
    type LoadingStep,
} from "@/components/EstimateInputSection";
import { appendProposalToHistory, fetchEstimate } from "@/lib/estimateApi";
import { useToast } from "@/hooks/use-toast";

export default function NewProposalPage() {
    const router = useRouter();
    const { toast } = useToast();
    const [projectDesc, setProjectDesc] = useState("");
    const [platforms, setPlatforms] = useState<string[]>([]);
    const [timeline, setTimeline] = useState("");
    const [uploadedFile, setUploadedFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [loadingStep, setLoadingStep] = useState<LoadingStep>("idle");
    const [error, setError] = useState<string | null>(null);

    const togglePlatform = useCallback((value: string) => {
        setPlatforms((prev) =>
            prev.includes(value)
                ? prev.filter((p) => p !== value)
                : [...prev, value],
        );
    }, []);

    const handleFileChange = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>) => {
            const file = e.target.files?.[0] || null;
            setUploadedFile(file);
            if (file) toast({ title: `File selected: ${file.name}` });
        },
        [toast],
    );

    const handleFileDrop = useCallback(
        (e: React.DragEvent<HTMLDivElement>) => {
            e.preventDefault();
            const file = e.dataTransfer.files?.[0] || null;
            setUploadedFile(file);
            if (file) toast({ title: `File selected: ${file.name}` });
        },
        [toast],
    );

    const handleGenerate = useCallback(async () => {
        const desc = projectDesc.trim();
        if (!desc && !uploadedFile) {
            toast({
                title: "Enter a description or upload a file",
                variant: "destructive",
            });
            return;
        }
        if (desc.length > 0 && desc.length < 10) {
            toast({
                title: "Description must be at least 10 characters",
                variant: "destructive",
            });
            return;
        }

        setLoading(true);
        setError(null);
        setLoadingStep("estimating");

        try {
            toast({ title: "Generating estimation..." });

            const raw = await fetchEstimate({
                project_description: desc || undefined,
                file: uploadedFile || undefined,
                platforms: platforms.length ? platforms : undefined,
                timeline: timeline || undefined,
            });

            appendProposalToHistory(raw, {
                title: projectDesc || uploadedFile?.name,
            });

            toast({ title: "Estimation ready!" });
            router.push("/dashboard");
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : "";
            const isNet =
                msg === "Failed to fetch" ||
                msg.includes("NetworkError") ||
                msg.includes("Load failed");
            const API_BASE =
                (typeof process !== "undefined" &&
                    process.env?.NEXT_PUBLIC_API_BASE) ||
                "http://localhost:8000";

            let userMsg: string;
            if (isNet) {
                userMsg = `Cannot reach API at ${API_BASE}. Make sure the backend is running.`;
            } else if (
                msg.includes("Authentication required") ||
                msg.includes("Session expired")
            ) {
                userMsg = msg;
                router.push("/login");
            } else {
                userMsg = msg || "Estimation failed.";
            }

            setError(userMsg);
            toast({
                title: "Estimation failed",
                description: userMsg,
                variant: "destructive",
            });
        } finally {
            setLoading(false);
            setLoadingStep("idle");
        }
    }, [projectDesc, platforms, timeline, uploadedFile, toast, router]);

    return (
        <div className="min-h-screen relative bg-background">
            <div className="fixed inset-0 pointer-events-none z-0 dot-grid opacity-30" />
            <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
                <div
                    className="absolute top-[-12%] right-[-8%] w-[550px] h-[550px] rounded-full opacity-60"
                    style={{
                        background:
                            "radial-gradient(circle, hsl(230 94% 68% / 0.1), transparent 55%)",
                        filter: "blur(90px)",
                        animation:
                            "aurora-float 20s ease-in-out infinite alternate",
                    }}
                />
                <div
                    className="absolute bottom-[5%] left-[-6%] w-[450px] h-[450px] rounded-full opacity-50"
                    style={{
                        background:
                            "radial-gradient(circle, hsl(270 88% 68% / 0.08), transparent 55%)",
                        filter: "blur(90px)",
                        animation:
                            "aurora-float 16s ease-in-out infinite alternate-reverse",
                    }}
                />
            </div>

            <nav
                className="sticky top-0 z-40 border-b border-border/30"
                style={{
                    background: "hsl(var(--card) / 0.6)",
                    backdropFilter: "blur(20px) saturate(1.5)",
                }}
            >
                <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/20 to-transparent pointer-events-none" />
                <div className="container mx-auto flex items-center justify-between h-14 px-4">
                    <Link
                        href="/dashboard"
                        className="flex items-center gap-2.5 group"
                    >
                        <div className="w-9 h-9 rounded-xl gradient-bg flex items-center justify-center shrink-0 shadow-lg shadow-primary/25 group-hover:shadow-primary/40 group-hover:scale-105 transition-all duration-300">
                            <Brain className="w-5 h-5 text-white" />
                        </div>
                        <span
                            className="text-lg font-bold hidden sm:block tracking-tight"
                            style={{ fontFamily: "'Sora', system-ui" }}
                        >
                            Neural Architects
                        </span>
                    </Link>
                    <div className="flex items-center gap-2">
                        <Link href="/dashboard">
                            <Button
                                variant="outline"
                                size="sm"
                                className="rounded-xl border-border/40 hover:border-primary/30 hover:bg-primary/5 text-xs font-medium"
                            >
                                Back to Dashboard
                            </Button>
                        </Link>
                    </div>
                </div>
            </nav>

            <div className="container mx-auto px-4 py-8 relative z-10">
                <EstimateInputSection
                    projectDesc={projectDesc}
                    platforms={platforms}
                    timeline={timeline}
                    uploadedFile={uploadedFile}
                    loading={loading}
                    loadingStep={loadingStep}
                    error={error}
                    onChangeProjectDesc={setProjectDesc}
                    onTogglePlatform={togglePlatform}
                    onChangeTimeline={setTimeline}
                    onFileChange={handleFileChange}
                    onFileDrop={handleFileDrop}
                    onGenerate={handleGenerate}
                />
            </div>
        </div>
    );
}
