"use client";

import React from "react";
import { motion } from "framer-motion";
import type { Module } from "@/types/dashboard";
import type { ProposalData, ResourceRow, TechRec } from "@/lib/utils";
import {
  EstimateStatCards,
  EstimateSummaryPills,
  EstimateSearchBar,
  EstimateFeaturesTable,
  TechStackSection,
  EstimateCtaBar,
} from "./estimate-results";
import type { StatCard } from "./estimate-results";

export interface EstimatesResultsSectionProps {
  estimateTableKey?: number;
  statCards: StatCard[];
  summaryData: { domain: string; platforms?: string[]; totalHours: number; timeline: string; confidence: number };
  proposalData: ProposalData | null;
  techStackStructured?: Record<string, unknown> | null;
  searchQuery: string;
  onSearchChange: (v: string) => void;
  modules: Module[];
  filteredModules: Module[];
  totalsByColumn: { frontend: number; backend: number; integration: number; testing: number; total: number };
  expandAll: () => void;
  collapseAll: () => void;
  toggleModule: (id: string) => void;
  toggleTask: (id: string) => void;
  taskExpanded: Record<string, boolean>;
  updateTaskName: (moduleId: string, taskId: string, name: string, childId?: string) => void;
  updateTaskField: (
    moduleId: string,
    taskId: string,
    field: "frontend" | "backend" | "integration" | "testing",
    value: number,
    childId?: string,
  ) => void;
  addTask: (moduleId: string) => void;
  addSubFeature: (moduleId: string, taskId: string) => void;
  deleteTask: (moduleId: string, taskId: string, childId?: string) => void;
  techStack: TechRec[];
  resources: ResourceRow[];
}

export function EstimatesResultsSection({
  estimateTableKey = 0,
  statCards,
  summaryData,
  proposalData,
  searchQuery,
  onSearchChange,
  modules,
  filteredModules,
  totalsByColumn,
  expandAll,
  collapseAll,
  toggleModule,
  toggleTask,
  taskExpanded,
  updateTaskName,
  updateTaskField,
  addTask,
  addSubFeature,
  deleteTask,
  techStack,
  techStackStructured,
  resources,
}: EstimatesResultsSectionProps) {
  return (
    <motion.div
      key="results"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* Estimate summary section */}
      <section className="rounded-2xl bg-card/30 backdrop-blur-sm overflow-hidden">
        <div className="p-5 md:p-6 space-y-5">
          <EstimateStatCards cards={statCards} />

          <EstimateSummaryPills summaryData={summaryData} proposalData={proposalData} />

          <EstimateSearchBar
            searchQuery={searchQuery}
            onSearchChange={onSearchChange}
            onExpandAll={expandAll}
            onCollapseAll={collapseAll}
          />
        </div>
      </section>

      <motion.section
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
      >
        <EstimateFeaturesTable
          key={`estimate-table-${estimateTableKey}-${modules.reduce((a, m) => a + m.tasks.length, 0)}`}
          filteredModules={filteredModules}
          totalsByColumn={totalsByColumn}
          searchQuery={searchQuery}
          taskExpanded={taskExpanded}
          onSearchChange={onSearchChange}
          toggleModule={toggleModule}
          toggleTask={toggleTask}
          updateTaskName={updateTaskName}
          updateTaskField={updateTaskField}
          addTask={addTask}
          addSubFeature={addSubFeature}
          deleteTask={deleteTask}
        />
      </motion.section>

      {(techStackStructured || techStack.length > 0) && (
        <TechStackSection techStackStructured={techStackStructured} techStack={techStack} />
      )}

      <EstimateCtaBar />
    </motion.div>
  );
}
