"use client";

import { useState } from "react";
import type { BuildOption } from "@/lib/api";
import { BUILD_OPTION_VALUES, BUILD_OPTION_LABELS } from "@/lib/constants";

interface EstimationFormProps {
  onSubmit: (data: {
    additionalDetails: string;
    buildOptions?: BuildOption[];
    timelineConstraint?: string;
  }) => void;
  loading: boolean;
}

export function EstimationForm({ onSubmit, loading }: EstimationFormProps) {
  const [additionalDetails, setAdditionalDetails] = useState("");
  const [buildOptions, setBuildOptions] = useState<BuildOption[]>([]);
  const [timelineConstraint, setTimelineConstraint] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (additionalDetails.trim().length < 10) {
      alert("Please provide additional details (at least 10 characters)");
      return;
    }

    onSubmit({
      additionalDetails,
      buildOptions: buildOptions.length ? buildOptions : undefined,
      timelineConstraint: timelineConstraint || undefined,
    });
  };

  const toggleBuildOption = (option: BuildOption) => {
    setBuildOptions((prev) =>
      prev.includes(option) ? prev.filter((x) => x !== option) : [...prev, option]
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-semibold text-slate-900 mb-6">
        Project Details
      </h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label
            htmlFor="additional-details"
            className="block text-sm font-medium text-slate-700 mb-2"
          >
            Additional Details *
          </label>
          <textarea
            id="additional-details"
            value={additionalDetails}
            onChange={(e) => setAdditionalDetails(e.target.value)}
            placeholder="Describe your project in detail..."
            className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={8}
            required
            minLength={10}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            What do you want to build?
          </label>
          <div
            role="group"
            aria-label="Build options (multi-select)"
            className="flex flex-wrap gap-3 p-3 border border-slate-200 rounded-lg bg-slate-50/50"
          >
            {BUILD_OPTION_VALUES.map((option) => (
              <label key={option} className="inline-flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={buildOptions.includes(option)}
                  onChange={() => toggleBuildOption(option)}
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-slate-700">{BUILD_OPTION_LABELS[option]}</span>
              </label>
            ))}
          </div>
          <p className="mt-1.5 text-xs text-slate-500">
            Select one or more: mobile, web, design, backend, admin
          </p>
        </div>

        <div>
          <label
            htmlFor="timeline"
            className="block text-sm font-medium text-slate-700 mb-2"
          >
            Timeline Constraint (Optional)
          </label>
          <input
            id="timeline"
            type="text"
            value={timelineConstraint}
            onChange={(e) => setTimelineConstraint(e.target.value)}
            placeholder="e.g., 2 months, ASAP"
            className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
        >
          {loading ? "Generating Estimation..." : "Generate Estimation"}
        </button>
      </form>
    </div>
  );
}
