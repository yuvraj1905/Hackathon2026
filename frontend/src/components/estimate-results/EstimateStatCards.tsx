"use client";

import React from "react";
import { motion } from "framer-motion";

export interface StatCard {
  label: string;
  value: string;
  meta?: string;
  color: string;
  iconColor: string;
  bg: string;
  icon: React.ElementType;
}

interface EstimateStatCardsProps {
  cards: StatCard[];
}

export function EstimateStatCards({ cards }: EstimateStatCardsProps) {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
      {cards.map((s, i) => {
        const Icon = s.icon;
        return (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className={`stat-bento shine-hover ${s.bg} ${i === 0 ? "lg:col-span-2 lg:flex-row lg:items-center lg:gap-6 lg:min-h-[140px]" : ""}`}
          >
            <div className={`stat-icon-wrap rounded-xl ${i === 0 ? "lg:mb-0 lg:h-14 lg:w-14" : ""}`}>
              <Icon className={`h-6 w-6 ${s.iconColor} ${i === 0 ? "lg:h-7 lg:w-7" : ""}`} />
            </div>
            <div className={i === 0 ? "lg:flex-1" : ""}>
              <span className={`stat-value ${s.color} ${i === 0 ? "lg:text-4xl xl:text-5xl" : ""}`}>{s.value}</span>
              <span className="stat-label mt-1 block">{s.label}</span>
              {s.meta && <span className="stat-meta block">{s.meta}</span>}
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
