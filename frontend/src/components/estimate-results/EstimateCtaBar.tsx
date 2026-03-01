"use client";

import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";

interface EstimateCtaBarProps {
  projectId?: string | null;
}

export function EstimateCtaBar({ projectId }: EstimateCtaBarProps) {
  const handleDownloadProposal = () => {
    if (!projectId) return;
    window.open(`/proposal/pdf/${projectId}`, "_blank");
  };

  return (
    <div className="cta-bar">
      <Button
        className="btn-primary-glow h-11 rounded-xl px-7 font-semibold"
        disabled={!projectId}
        onClick={handleDownloadProposal}
      >
        <Download className="relative z-10 mr-2 h-4 w-4" />
        <span className="relative z-10">Download Proposal</span>
      </Button>
    </div>
  );
}
