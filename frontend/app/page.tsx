"use client";

import { useState } from "react";
import { estimateProject, modifyScope, APIError, type EstimationResponse } from "@/lib/api";
import { EstimationTable } from "@/components/EstimationTable";
import { EstimationSummary } from "@/components/EstimationSummary";
import { ScopeModifier } from "@/components/ScopeModifier";

export default function Home() {
  const [projectDescription, setProjectDescription] = useState("");
  const [budgetRange, setBudgetRange] = useState("");
  const [timelineConstraint, setTimelineConstraint] = useState("");
  const [results, setResults] = useState<EstimationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [modifying, setModifying] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (projectDescription.trim().length < 10) {
      alert("Please provide a more detailed project description (at least 10 characters)");
      return;
    }

    setLoading(true);
    setResults(null);

    try {
      const data = await estimateProject({
        project_description: projectDescription,
        budget_range: budgetRange || null,
        timeline_constraint: timelineConstraint || null,
      });

      setResults(data);
    } catch (error) {
      console.error("Error:", error);

      if (error instanceof APIError) {
        alert(error.message);
      } else {
        alert("Failed to generate estimation. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleModify = async (instruction: string) => {
    if (!results) return;

    setModifying(true);

    try {
      const currentFeatures = results.estimation.features.map((f) => ({
        name: f.name,
        category: f.description,
        complexity: f.complexity,
      }));

      const modificationData = await modifyScope({
        current_features: currentFeatures,
        instruction,
      });

      setResults({
        ...results,
        estimation: {
          ...results.estimation,
          total_hours: modificationData.total_hours,
          min_hours: modificationData.min_hours,
          max_hours: modificationData.max_hours,
          features: modificationData.features,
        },
      });

      alert(`Changes applied: ${modificationData.changes_summary}`);
    } catch (error) {
      console.error("Error:", error);

      if (error instanceof APIError) {
        alert(error.message);
      } else {
        alert("Failed to modify scope. Please try again.");
      }
    } finally {
      setModifying(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <header className="mb-12 text-center">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">
            Presales Estimation Engine
          </h1>
          <p className="text-slate-600">
            AI-powered project estimation for GeekyAnts presales team
          </p>
        </header>

        <div className="grid gap-8">
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
                  className="text-black w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
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
                  className="text-black w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                  className="text-black w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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

          {results && (
            <div className="space-y-6">
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-semibold text-slate-900">
                    Estimation Results
                  </h2>
                  <span className="text-sm bg-blue-100 text-blue-800 px-3 py-1 rounded-full">
                    {results.domain_detection.detected_domain.toUpperCase()}
                  </span>
                </div>

                <p className="text-sm text-slate-600 mb-4">
                  {results.domain_detection.reasoning}
                </p>

                <div className="border-t border-slate-200 pt-4">
                  <h3 className="text-lg font-semibold text-slate-800 mb-3">
                    Proposal Summary
                  </h3>
                  <div className="space-y-3 text-sm">
                    <div>
                      <p className="font-medium text-slate-700 mb-1">
                        Executive Summary
                      </p>
                      <p className="text-slate-600">{results.proposal.executive_summary}</p>
                    </div>
                    <div>
                      <p className="font-medium text-slate-700 mb-1">Timeline</p>
                      <p className="text-slate-600">
                        {results.proposal.timeline_weeks} weeks
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <EstimationSummary
                features={results.estimation.features}
                techStack={results.tech_stack}
                domainConfidence={results.domain_detection.confidence}
              />

              <ScopeModifier onModify={handleModify} loading={modifying} />

              <EstimationTable
                initialFeatures={results.estimation.features}
                onFeaturesChange={(updatedFeatures) => {
                  setResults({
                    ...results,
                    estimation: {
                      ...results.estimation,
                      features: updatedFeatures,
                    },
                  });
                }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
