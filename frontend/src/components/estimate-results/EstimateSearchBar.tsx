"use client";

import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface EstimateSearchBarProps {
  searchQuery: string;
  onSearchChange: (v: string) => void;
  onExpandAll: () => void;
  onCollapseAll: () => void;
}

export function EstimateSearchBar({
  searchQuery,
  onSearchChange,
  onExpandAll,
  onCollapseAll,
}: EstimateSearchBarProps) {
  return (
    <div className="flex flex-col items-stretch justify-between gap-3 sm:flex-row sm:items-center">
      <div className="relative flex-1 max-w-sm">
        <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground/50" />
        <Input
          placeholder="Search features…"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="h-10 rounded-xl border-border/40 bg-card/40 pl-10 focus:ring-2 focus:ring-primary/20"
        />
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onExpandAll}
          className="rounded-xl border-border/40 text-xs hover:border-primary/25 hover:bg-primary/5"
        >
          Expand All
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onCollapseAll}
          className="rounded-xl border-border/40 text-xs hover:border-primary/25 hover:bg-primary/5"
        >
          Collapse All
        </Button>
      </div>
    </div>
  );
}
