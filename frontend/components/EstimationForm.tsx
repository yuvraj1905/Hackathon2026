"use client";

import { useState } from "react";

interface EstimationFormProps {
  onSubmit: (data: {
    projectDescription: string;
    budgetRange?: string;
    timelineConstraint?: string;
  }) => void;
  loading: boolean;
}

export function EstimationForm({ onSubmit, loading }: EstimationFormProps) {
  const [projectDescription, setProjectDescription] = useState("");
  const [budgetRange, setBudgetRange] = useState("");
  const [timelineConstraint, setTimelineConstraint] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (projectDescription.trim().length < 10) {
      alert("Please provide a more detailed project description (at least 10 characters)");
      return;
    }

    onSubmit({
      projectDescription,
      budgetRange: budgetRange || undefined,
      timelineConstraint: timelineConstraint || undefined,
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-semibold text-slate-900 mb-6">
        Project Details
      </h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label
            htmlFor="description"
            className="block text-sm font-medium text-slate-700 mb-2"
          >
            Project Description *
          </label>
          <textarea
            id="description"
            value={projectDescription}
            onChange={(e) => setProjectDescription(e.target.value)}
            placeholder="Describe your project in detail..."
            className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={8}
            required
            minLength={10}
          />
        </div>

        <div>
          <label
            htmlFor="budget"
            className="block text-sm font-medium text-slate-700 mb-2"
          >
            Budget Range (Optional)
          </label>
          <input
            id="budget"
            type="text"
            value={budgetRange}
            onChange={(e) => setBudgetRange(e.target.value)}
            placeholder="e.g., 2 lac INR, $10k-$20k"
            className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
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
