"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Brain, History as HistoryIcon, Search, Calendar, FileText, ArrowRight, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const mockHistory = [
  { id: "1", title: "Hotel Booking Platform", domain: "Hospitality", totalSP: 1091, modules: 17, features: 68, createdAt: "2026-02-25", status: "completed" },
  { id: "2", title: "E-Commerce Marketplace", domain: "E-Commerce", totalSP: 845, modules: 12, features: 52, createdAt: "2026-02-22", status: "completed" },
  { id: "3", title: "FinTech Payment Gateway", domain: "FinTech", totalSP: 1320, modules: 20, features: 78, createdAt: "2026-02-18", status: "completed" },
  { id: "4", title: "Healthcare Patient Portal", domain: "Healthcare", totalSP: 680, modules: 9, features: 38, createdAt: "2026-02-14", status: "draft" },
  { id: "5", title: "EdTech Learning Management System", domain: "EdTech", totalSP: 950, modules: 14, features: 61, createdAt: "2026-02-10", status: "completed" },
];

export default function HistoryPage() {
  const [search, setSearch] = useState("");

  const filtered = mockHistory.filter(h =>
    h.title.toLowerCase().includes(search.toLowerCase()) ||
    h.domain.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-background">
      <nav className="sticky top-0 z-40 bg-background/80 backdrop-blur-xl border-b border-border/50">
        <div className="container mx-auto flex items-center justify-between h-14 px-4">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg gradient-bg flex items-center justify-center">
              <Brain className="w-4 h-4 text-primary-foreground" />
            </div>
            <span className="font-display text-lg font-bold">Neural Architects</span>
          </Link>
          <div className="flex items-center gap-2">
            <Link href="/dashboard">
              <Button variant="outline" size="sm">+ New Estimation</Button>
            </Link>
            <Link href="/">
              <Button variant="ghost" size="sm"><LogOut className="w-4 h-4" /></Button>
            </Link>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-display font-bold flex items-center gap-2">
              <HistoryIcon className="w-6 h-6 text-primary" />
              Estimation History
            </h1>
            <p className="text-muted-foreground text-sm mt-1">{mockHistory.length} proposals generated</p>
          </div>
          <div className="relative w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search by title or domain..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 h-9"
            />
          </div>
        </div>

        <div className="space-y-3">
          {filtered.map((item, i) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="glass-card-hover p-5 flex items-center justify-between group cursor-pointer"
            >
              <div className="flex items-center gap-5">
                <div className="w-11 h-11 rounded-lg bg-primary/10 flex items-center justify-center">
                  <FileText className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-display font-semibold">{item.title}</h3>
                  <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                    <span className="px-2 py-0.5 bg-muted rounded-full">{item.domain}</span>
                    <span className="flex items-center gap-1"><Calendar className="w-3 h-3" />{item.createdAt}</span>
                    <span>{item.modules} modules · {item.features} features</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-6">
                <div className="text-right">
                  <p className="font-display font-bold text-lg text-primary">{item.totalSP} SP</p>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    item.status === "completed"
                      ? "bg-success/10 text-success"
                      : "bg-warning/10 text-warning"
                  }`}>
                    {item.status}
                  </span>
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
