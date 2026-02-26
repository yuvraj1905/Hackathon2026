"use client";

import { useState, useEffect } from "react";

interface Feature {
  name: string;
  description: string;
  complexity: "low" | "medium" | "high" | "very_high";
  estimated_hours: number;
  dependencies: string[];
  confidence_score: number;
}

interface EstimationTableProps {
  initialFeatures: Feature[];
  onFeaturesChange?: (features: Feature[]) => void;
}

const COMPLEXITY_BASE_HOURS = {
  low: 28,
  medium: 72,
  high: 140,
  very_high: 200,
};

const BUFFER_MULTIPLIER = 1.15;
const MVP_FACTOR = 0.75;

export function EstimationTable({
  initialFeatures,
  onFeaturesChange,
}: EstimationTableProps) {
  const [features, setFeatures] = useState<Feature[]>(initialFeatures);

  useEffect(() => {
    setFeatures(initialFeatures);
  }, [initialFeatures]);

  const calculateHours = (complexity: string): number => {
    const baseHours = COMPLEXITY_BASE_HOURS[complexity as keyof typeof COMPLEXITY_BASE_HOURS] || 72;
    return Math.round(baseHours * BUFFER_MULTIPLIER * MVP_FACTOR * 10) / 10;
  };

  const handleComplexityChange = (index: number, newComplexity: string) => {
    const updatedFeatures = [...features];
    const recalculatedHours = calculateHours(newComplexity);

    updatedFeatures[index] = {
      ...updatedFeatures[index],
      complexity: newComplexity as Feature["complexity"],
      estimated_hours: recalculatedHours,
    };

    setFeatures(updatedFeatures);
    onFeaturesChange?.(updatedFeatures);
  };

  const totalHours = features.reduce(
    (sum, feature) => sum + feature.estimated_hours,
    0
  );

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case "low":
        return "bg-green-100 text-green-800";
      case "medium":
        return "bg-yellow-100 text-yellow-800";
      case "high":
        return "bg-orange-100 text-orange-800";
      case "very_high":
        return "bg-red-100 text-red-800";
      default:
        return "bg-slate-100 text-slate-800";
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-semibold text-slate-900">
          Feature Breakdown
        </h3>
        <div className="text-sm text-slate-600">
          Total: <span className="font-bold text-slate-900">{totalHours.toFixed(1)}h</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b-2 border-slate-200">
            <tr>
              <th className="text-left px-4 py-3 font-semibold text-slate-700">
                Feature
              </th>
              <th className="text-left px-4 py-3 font-semibold text-slate-700">
                Category
              </th>
              <th className="text-left px-4 py-3 font-semibold text-slate-700">
                Complexity
              </th>
              <th className="text-right px-4 py-3 font-semibold text-slate-700">
                Hours
              </th>
              <th className="text-center px-4 py-3 font-semibold text-slate-700">
                Confidence
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {features.map((feature, idx) => (
              <tr key={idx} className="hover:bg-slate-50 transition-colors">
                <td className="px-4 py-3 text-slate-900 font-medium">
                  {feature.name}
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {feature.description}
                </td>
                <td className="px-4 py-3">
                  <select
                    value={feature.complexity}
                    onChange={(e) => handleComplexityChange(idx, e.target.value)}
                    className={`px-3 py-1 rounded text-xs font-medium border-0 cursor-pointer focus:ring-2 focus:ring-blue-500 ${getComplexityColor(
                      feature.complexity
                    )}`}
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="very_high">Very High</option>
                  </select>
                </td>
                <td className="px-4 py-3 text-right font-semibold text-slate-900">
                  {feature.estimated_hours.toFixed(1)}h
                </td>
                <td className="px-4 py-3 text-center">
                  <span className="text-xs text-slate-600">
                    {Math.round(feature.confidence_score * 100)}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot className="bg-slate-50 border-t-2 border-slate-200">
            <tr>
              <td colSpan={3} className="px-4 py-3 text-right font-bold text-slate-900">
                Total Estimated Hours:
              </td>
              <td className="px-4 py-3 text-right font-bold text-slate-900 text-base">
                {totalHours.toFixed(1)}h
              </td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>

      <div className="mt-4 p-4 bg-blue-50 rounded-lg">
        <p className="text-xs text-slate-600">
          <span className="font-semibold">Note:</span> Complexity changes will
          automatically recalculate hours using base rates (Low: 28h, Medium: 72h,
          High: 140h, Very High: 200h) with 15% buffer and MVP factor applied.
        </p>
      </div>
    </div>
  );
}
