"use client";

import React, { ChangeEvent, DragEvent } from "react";
import { motion } from "framer-motion";
import {
  AlertCircle,
  ArrowRight,
  Brain,
  CheckCircle,
  ChevronDown,
  FileText,
  Loader2,
  Send,
  Sparkles,
  Upload,
} from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { LOADING_STEPS, PLATFORM_OPTIONS } from "@/lib/utils";

export type LoadingStep = "idle" | "uploading" | "estimating";

interface EstimateInputSectionProps {
  projectDesc: string;
  platforms: string[];
  timeline: string;
  uploadedFile: File | null;
  loading: boolean;
  loadingStep?: LoadingStep;
  error: string | null;
  onChangeProjectDesc: (value: string) => void;
  onTogglePlatform: (value: string) => void;
  onChangeTimeline: (value: string) => void;
  onFileChange: (e: ChangeEvent<HTMLInputElement>) => void;
  onFileDrop: (e: DragEvent<HTMLDivElement>) => void;
  onGenerate: () => void;
}

const LoadingOverlay = () => {
  const [step, setStep] = React.useState(0);

  React.useEffect(() => {
    const id = setInterval(
      () => setStep((s) => Math.min(s + 1, LOADING_STEPS.length - 1)),
      3000,
    );
    return () => clearInterval(id);
  }, []);

  return (
    <div className="flex flex-col items-center gap-10 py-20">
      <div className="relative">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
          className="absolute inset-[-16px] rounded-full"
          style={{
            background:
              "conic-gradient(from 0deg, hsl(230 94% 68% / 0.3), hsl(270 88% 68% / 0.3), hsl(200 90% 60% / 0.2), hsl(230 94% 68% / 0.3))",
            filter: "blur(12px)",
          }}
        />
        <div className="gradient-bg relative flex h-24 w-24 items-center justify-center rounded-full shadow-2xl shadow-primary/30">
          <Brain className="h-11 w-11 text-white" />
        </div>
        <span className="pulse-ring bg-primary/15" />
        <span className="pulse-ring bg-primary/10" style={{ animationDelay: "0.8s" }} />
      </div>

      <div className="w-full max-w-sm space-y-2.5">
        {LOADING_STEPS.map((s, i) => {
          const Icon = s.icon;
          const done = i < step;
          const active = i === step;
          return (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, x: -16 }}
              animate={{ opacity: i <= step ? 1 : 0.2, x: 0 }}
              transition={{ delay: i * 0.1, duration: 0.4 }}
              className={`flex items-center gap-3.5 rounded-xl px-5 py-3 transition-all duration-500 ${active ? "bg-primary/8 border border-primary/15 shadow-lg shadow-primary/5" : ""
                }`}
            >
              {done ? (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 400 }}
                >
                  <CheckCircle className="h-5 w-5 shrink-0 text-emerald-400" />
                </motion.div>
              ) : active ? (
                <Loader2 className={`h-5 w-5 shrink-0 ${s.color} animate-spin`} />
              ) : (
                <Icon className="h-5 w-5 shrink-0 text-muted-foreground/30" />
              )}
              <span
                className={`text-sm font-medium transition-colors duration-300 ${active
                    ? "text-foreground"
                    : done
                      ? "text-emerald-400/80"
                      : "text-muted-foreground/30"
                  }`}
              >
                {s.label}
              </span>
              {active && (
                <motion.div
                  className="ml-auto flex gap-1"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  {[0, 1, 2].map((d) => (
                    <motion.span
                      key={d}
                      className="h-1.5 w-1.5 rounded-full bg-primary"
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 1.2, repeat: Infinity, delay: d * 0.2 }}
                    />
                  ))}
                </motion.div>
              )}
            </motion.div>
          );
        })}
      </div>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="max-w-xs text-center text-xs text-muted-foreground/60"
      >
        Our AI agents are analyzing your project. This typically takes 15–30 seconds.
      </motion.p>
    </div>
  );
};

export function EstimateInputSection({
  projectDesc,
  platforms,
  timeline,
  uploadedFile,
  loading,
  loadingStep = "idle",
  error,
  onChangeProjectDesc,
  onTogglePlatform,
  onChangeTimeline,
  onFileChange,
  onFileDrop,
  onGenerate,
}: EstimateInputSectionProps) {
  const getButtonContent = () => {
    if (!loading) {
      return (
        <>
          <Send className="relative z-10 mr-2.5 h-5 w-5" />
          <span className="relative z-10">Generate Estimation</span>
          <ArrowRight className="relative z-10 ml-2 h-4 w-4 opacity-60" />
        </>
      );
    }

    if (loadingStep === "uploading") {
      return (
        <>
          <Loader2 className="relative z-10 mr-2.5 h-5 w-5 animate-spin" />
          <span className="relative z-10">Uploading Document...</span>
        </>
      );
    }

    return (
      <>
        <Loader2 className="relative z-10 mr-2.5 h-5 w-5 animate-spin" />
        <span className="relative z-10">Generating Estimation...</span>
      </>
    );
  };
  return (
    <motion.div
      key="input"
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="mx-auto max-w-3xl"
    >
      <div className="mb-14 text-center">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="badge-glow mx-auto mb-6 text-primary"
        >
          <Sparkles className="h-3.5 w-3.5" /> AI-Powered Estimation
        </motion.div>
        <motion.h1
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="mb-5 text-4xl font-bold leading-[1.1] tracking-tight md:text-5xl lg:text-[3.5rem]"
          style={{ fontFamily: "'Sora', system-ui" }}
        >
          <span className="gradient-text-animated">Idea to proposal</span>
          <br />
          <span className="text-foreground">in minutes, not hours</span>
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.25 }}
          className="mx-auto max-w-lg text-base leading-relaxed text-muted-foreground md:text-lg"
        >
          Describe your project. Our AI agents will break it down into features, estimate
          hours, recommend a tech stack, and draft a client-ready proposal.
        </motion.p>
      </div>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 flex items-start gap-3 rounded-2xl border border-destructive/40 bg-destructive/8 p-5"
        >
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-destructive" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-destructive">Estimation failed</p>
            <p className="mt-1 break-words text-xs text-muted-foreground">{error}</p>
          </div>
        </motion.div>
      )}

      <div className="card-hero relative z-10 space-y-8 p-6 md:p-10">
        {loading ? (
          <LoadingOverlay />
        ) : (
          <>
            <div>
              <div className="mb-2.5 flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm font-semibold">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  Additional Details
                </label>
                <span
                  className={`tabular-nums text-xs font-mono ${projectDesc.length > 0 && projectDesc.length < 10
                      ? "text-destructive"
                      : "text-muted-foreground/60"
                    }`}
                >
                  {projectDesc.length}
                </span>
              </div>
              <Textarea
                placeholder="Build a healthcare patient management system with appointment booking, real-time telemedicine, billing integration, and role-based access for doctors, nurses, and administrators…"
                value={projectDesc}
                onChange={(e) => onChangeProjectDesc(e.target.value)}
                className="min-h-[170px] resize-none rounded-xl border-border/40 bg-background/40 text-sm leading-relaxed placeholder:text-muted-foreground/50 transition-all focus:border-primary/40 focus:ring-2 focus:ring-primary/30"
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Platforms
                </label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className="h-10 w-full justify-between rounded-xl border-border/40 bg-background/40 font-normal hover:border-primary/25 hover:bg-background/40 focus:ring-2 focus:ring-primary/25"
                    >
                      <span
                        className={platforms.length ? "text-foreground" : "text-muted-foreground"}
                      >
                        {platforms.length
                          ? platforms
                            .map(
                              (p) =>
                                PLATFORM_OPTIONS.find((o) => o.value === p)?.label ?? p,
                            )
                            .join(", ")
                          : "Select platforms…"}
                      </span>
                      <ChevronDown className="h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent
                    className="w-[var(--radix-popover-trigger-width)] rounded-xl border-border/40 p-2"
                    align="start"
                  >
                    <div className="flex flex-col gap-1">
                      {PLATFORM_OPTIONS.map((opt) => (
                        <label
                          key={opt.value}
                          className="flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-sm hover:bg-muted/50"
                        >
                          <Checkbox
                            checked={platforms.includes(opt.value)}
                            onCheckedChange={() => onTogglePlatform(opt.value)}
                          />
                          <span>{opt.label}</span>
                        </label>
                      ))}
                    </div>
                  </PopoverContent>
                </Popover>
              </div>
              <div>
                <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Timeline
                </label>
                <Input
                  placeholder="3 months"
                  value={timeline}
                  onChange={(e) => onChangeTimeline(e.target.value)}
                  className="h-10 rounded-xl border-border/40 bg-background/40 focus:ring-2 focus:ring-primary/25"
                />
              </div>
            </div>

            <div
              className={`upload-zone group ${uploadedFile ? "has-file" : ""}`}
              onDragOver={(e) => e.preventDefault()}
              onDrop={onFileDrop}
              onClick={() => document.getElementById("file-upload-input")?.click()}
            >
              <input
                id="file-upload-input"
                type="file"
                accept=".pdf,.docx,.xlsx,.csv,.txt"
                className="hidden"
                onChange={onFileChange}
              />
              {uploadedFile ? (
                <div className="flex flex-col items-center gap-2">
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/15">
                    <CheckCircle className="h-7 w-7 text-emerald-400" />
                  </div>
                  <p className="text-sm font-semibold text-emerald-400">{uploadedFile.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {(uploadedFile.size / 1024).toFixed(1)} KB · click to replace
                  </p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/8 transition-colors group-hover:bg-primary/15">
                    <Upload className="h-7 w-7 text-primary/70 transition-colors group-hover:text-primary" />
                  </div>
                  <p className="text-sm font-medium">
                    Drag & drop or <span className="text-primary">browse</span>
                  </p>
                  <p className="text-xs text-muted-foreground/60">PDF, DOCX, XLSX, CSV, TXT</p>
                </div>
              )}
            </div>

            <Button
              className="btn-primary-glow h-14 w-full text-base font-semibold tracking-wide"
              onClick={onGenerate}
              disabled={
                loading || (projectDesc.trim().length > 0 && projectDesc.trim().length < 10)
              }
            >
              {getButtonContent()}
            </Button>
          </>
        )}
      </div>
    </motion.div>
  );
}