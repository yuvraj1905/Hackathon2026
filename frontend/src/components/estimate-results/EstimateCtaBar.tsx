"use client";

import { CheckCircle, Download, Share2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export function EstimateCtaBar() {
  return (
    <div className="cta-bar">
      <Button className="btn-primary-glow h-11 rounded-xl px-7 font-semibold">
        <CheckCircle className="relative z-10 mr-2 h-4 w-4" />
        <span className="relative z-10">Approve Estimation</span>
      </Button>
      <Button
        variant="outline"
        className="h-11 rounded-xl border-border/40 px-6 font-medium transition-all hover:border-primary/25 hover:bg-primary/5"
      >
        <Download className="mr-2 h-4 w-4" /> Download PDF
      </Button>
      <Button
        variant="outline"
        className="h-11 rounded-xl border-border/40 px-6 font-medium transition-all hover:border-accent/25 hover:bg-accent/5"
      >
        <Share2 className="mr-2 h-4 w-4" /> Share
      </Button>
    </div>
  );
}
