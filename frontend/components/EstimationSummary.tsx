"use client";

import { useMemo } from "react";

interface Feature {
  name: string;
  description: string;
  complexity: "low" | "medium" | "high" | "very_high";
  estimated_hours: number;
  dependencies: string[];
  confidence_score: number;
}

interface TechStack {
  frontend: string[];
  backend: string[];
  database: string[];
  infrastructure: string[];
  third_party_services: string[];
  justification: string;
}

interface EstimationSummaryProps {
  features: Feature[];
  techStack: TechStack;
  domainConfidence: number;
}

export function EstimationSummary({
  features,
  techStack,
  domainConfidence,
}: EstimationSummaryProps) {
  const totalHours = useMemo(() => {
    return features.reduce((sum, feature) => sum + feature.estimated_hours, 0);
  }, [features]);

  const bufferedTotal = useMemo(() => {
    return totalHours * 1.15;
  }, [totalHours]);

  const minHours = useMemo(() => {
    return totalHours * 0.85;
  }, [totalHours]);

  const maxHours = useMemo(() => {
    return totalHours * 1.35;
  }, [totalHours]);

  const avgConfidence = useMemo(() => {
    if (features.length === 0) return 0;
    const sum = features.reduce((acc, f) => acc + f.confidence_score, 0);
    return sum / features.length;
  }, [features]);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h3 className="text-xl font-semibold text-slate-900 mb-6">
        Estimation Summary
      </h3>

      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-5 rounded-lg border border-blue-200">
            <p className="text-sm text-blue-700 font-medium mb-1">
              Total Hours
            </p>
            <p className="text-3xl font-bold text-blue-900">
              {totalHours.toFixed(1)}h
            </p>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-5 rounded-lg border border-purple-200">
            <p className="text-sm text-purple-700 font-medium mb-1">
              Buffered Total
            </p>
            <p className="text-3xl font-bold text-purple-900">
              {bufferedTotal.toFixed(1)}h
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="bg-slate-50 p-4 rounded-lg">
            <p className="text-xs text-slate-600 mb-1">Min Estimate</p>
            <p className="text-lg font-semibold text-slate-900">
              {minHours.toFixed(1)}h
            </p>
          </div>
          <div className="bg-slate-50 p-4 rounded-lg">
            <p className="text-xs text-slate-600 mb-1">Max Estimate</p>
            <p className="text-lg font-semibold text-slate-900">
              {maxHours.toFixed(1)}h
            </p>
          </div>
        </div>

        <div className="border-t border-slate-200 pt-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-slate-700">
              Overall Confidence
            </p>
            <span className="text-2xl font-bold text-slate-900">
              {Math.round(avgConfidence * 100)}%
            </span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${avgConfidence * 100}%` }}
            ></div>
          </div>
        </div>

        <div className="border-t border-slate-200 pt-4">
          <h4 className="text-sm font-semibold text-slate-800 mb-3">
            Suggested Tech Stack
          </h4>
          <div className="space-y-2 text-sm">
            <div className="flex items-start">
              <span className="font-medium text-slate-700 w-28 flex-shrink-0">
                Frontend:
              </span>
              <span className="text-slate-600">
                {techStack.frontend.join(", ")}
              </span>
            </div>
            <div className="flex items-start">
              <span className="font-medium text-slate-700 w-28 flex-shrink-0">
                Backend:
              </span>
              <span className="text-slate-600">
                {techStack.backend.join(", ")}
              </span>
            </div>
            <div className="flex items-start">
              <span className="font-medium text-slate-700 w-28 flex-shrink-0">
                Database:
              </span>
              <span className="text-slate-600">
                {techStack.database.join(", ")}
              </span>
            </div>
            <div className="flex items-start">
              <span className="font-medium text-slate-700 w-28 flex-shrink-0">
                Infrastructure:
              </span>
              <span className="text-slate-600">
                {techStack.infrastructure.join(", ")}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-slate-50 p-4 rounded-lg">
          <p className="text-xs text-slate-600">
            <span className="font-semibold">Timeline:</span> Approximately{" "}
            {(totalHours / 40).toFixed(1)} weeks at 40 hours/week
          </p>
        </div>
      </div>
    </div>
  );
}
