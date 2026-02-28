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
    </div>
  );
}
