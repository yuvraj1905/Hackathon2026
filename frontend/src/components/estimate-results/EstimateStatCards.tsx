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
    <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-5">
      {cards.map((s, i) => {
        const Icon = s.icon;
        const isHero = i === 0;
        return (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + i * 0.06, duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
            className={`shine-hover ${s.bg} ${isHero ? "stat-hero lg:col-span-2" : "stat-bento"}`}
          >
            <div className="stat-icon-wrap">
              <Icon className={`h-5 w-5 ${s.iconColor} ${isHero ? "lg:h-7 lg:w-7" : ""}`} />
            </div>
            <div className={isHero ? "min-w-0 lg:flex-1" : ""}>
              <span className={`stat-value ${s.color}`}>{s.value}</span>
              <span className="stat-label block">{s.label}</span>
              {s.meta && <span className="stat-meta block">{s.meta}</span>}
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
