"use client";

import { useMemo } from "react";

interface PlanningBreakdownProps {
  planning: {
    phase_split: Record<string, number>;
    team_recommendation: Record<string, number>;
    category_breakdown: Record<string, number>;
  };
}

export function PlanningBreakdown({ planning }: PlanningBreakdownProps) {
  const totalPhaseHours = useMemo(() => {
    return Object.values(planning.phase_split).reduce((sum, hours) => sum + hours, 0);
  }, [planning.phase_split]);

  const phasePercentages = useMemo(() => {
    return Object.entries(planning.phase_split).map(([phase, hours]) => ({
      phase,
      hours,
      percentage: totalPhaseHours > 0 ? (hours / totalPhaseHours) * 100 : 0,
    }));
  }, [planning.phase_split, totalPhaseHours]);

  const totalTeamSize = useMemo(() => {
    return Object.values(planning.team_recommendation).reduce((sum, count) => sum + count, 0);
  }, [planning.team_recommendation]);

  const getPhaseColor = (phase: string) => {
    const colors: Record<string, string> = {
      frontend: "bg-blue-500",
      backend: "bg-green-500",
      qa: "bg-orange-500",
      pm_ba: "bg-purple-500",
    };
    return colors[phase] || "bg-slate-500";
  };

  const getPhaseLabel = (phase: string) => {
    const labels: Record<string, string> = {
      frontend: "Frontend",
      backend: "Backend",
      qa: "QA",
      pm_ba: "PM/BA",
    };
    return labels[phase] || phase;
  };

  return (
    <div className="grid md:grid-cols-3 gap-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">
          Recommended Team
        </h3>
        <div className="space-y-3">
          {Object.entries(planning.team_recommendation).map(([role, count]) => (
            <div key={role} className="flex items-center justify-between">
              <span className="text-sm text-slate-600">{role}</span>
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold text-slate-900">{count}</span>
                <span className="text-xs text-slate-500">
                  {count === 1 ? "person" : "people"}
                </span>
              </div>
            </div>
          ))}
          <div className="pt-3 border-t border-slate-200">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-slate-700">Total Team</span>
              <span className="text-xl font-bold text-blue-600">{totalTeamSize}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">
          Phase-wise Effort
        </h3>
        <div className="space-y-3">
          {phasePercentages.map(({ phase, hours, percentage }) => (
            <div key={phase}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-slate-600 capitalize">
                  {getPhaseLabel(phase)}
                </span>
                <span className="text-sm font-semibold text-slate-900">
                  {hours}h ({percentage.toFixed(0)}%)
                </span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-2">
                <div
                  className={`${getPhaseColor(phase)} h-2 rounded-full transition-all duration-300`}
                  style={{ width: `${percentage}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 pt-4 border-t border-slate-200">
          <p className="text-xs text-slate-600">
            Distribution based on industry-standard ratios
          </p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">
          Module Categories
        </h3>
        <div className="space-y-2">
          {Object.entries(planning.category_breakdown)
            .sort((a, b) => b[1] - a[1])
            .map(([category, hours]) => (
              <div
                key={category}
                className="flex items-center justify-between bg-slate-50 px-3 py-2 rounded-lg"
              >
                <span className="text-sm text-slate-700 font-medium">
                  {category}
                </span>
                <span className="text-sm font-bold text-slate-900">{hours}h</span>
              </div>
            ))}
        </div>
        {Object.keys(planning.category_breakdown).length === 0 && (
          <p className="text-sm text-slate-500 text-center py-4">
            No categories available
          </p>
        )}
      </div>
    </div>
  );
}
