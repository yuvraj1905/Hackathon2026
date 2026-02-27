"use client";

import { useState } from "react";
import { estimateProject, modifyScope, APIError, type EstimationResponse, type BuildOption } from "@/lib/api";
import { BUILD_OPTION_VALUES, BUILD_OPTION_LABELS } from "@/lib/constants";
import { EstimationTable } from "@/components/EstimationTable";
import { EstimationSummary } from "@/components/EstimationSummary";
import { ScopeModifier } from "@/components/ScopeModifier";
import { PlanningBreakdown } from "@/components/PlanningBreakdown";

export default function Home() {
  const [additionalDetails, setAdditionalDetails] = useState("");
  const [buildOptions, setBuildOptions] = useState<BuildOption[]>([]);
  const [timelineConstraint, setTimelineConstraint] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [results, setResults] = useState<EstimationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [modifying, setModifying] = useState(false);
  const [toast, setToast] = useState<{ type: "error" | "success"; message: string } | null>(null);

  const showToast = (type: "error" | "success", message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 3500);
  };

  const validateFile = (file: File): string | null => {
    const maxBytes = 10 * 1024 * 1024;
    if (file.size > maxBytes) {
      return "File size must be under 10MB.";
    }
    const ext = file.name.split(".").pop()?.toLowerCase() || "";
    const allowed = new Set(["pdf", "docx", "xlsx"]);
    if (!allowed.has(ext)) {
      return "Unsupported file type. Please upload PDF, DOCX, or XLSX.";
    }
    return null;
  };

  const handleFileSelect = (file: File | null) => {
    if (!file) return;
    const error = validateFile(file);
    if (error) {
      showToast("error", error);
      return;
    }
    setSelectedFile(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!additionalDetails.trim() && !selectedFile) {
      showToast("error", "Please provide additional details (at least 10 characters), upload a document, or both.");
      return;
    }
    if (additionalDetails.trim().length < 10 && !selectedFile) {
      showToast("error", "Additional details must be at least 10 characters when no document is uploaded.");
      return;
    }

    setLoading(true);
    setResults(null);

    const payload = {
      additional_details: additionalDetails.trim() || undefined,
      build_options: buildOptions.length ? buildOptions : undefined,
      timeline_constraint: timelineConstraint || null,
      file: selectedFile,
    };

    try {
      const data = await estimateProject(payload);
      setResults(data);
    } catch (error) {
      console.error("Error:", error);

      if (error instanceof APIError) {
        showToast("error", error.message);
      } else {
        showToast("error", "Network failure. Please try again.");
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
        <header className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">
            Presales Estimation Engine
          </h1>
          <p className="text-slate-600">
            AI-powered project estimation for GeekyAnts presales team
          </p>
        </header>

        {toast && (
          <div
            className={`mb-6 rounded-lg px-4 py-3 text-sm font-medium transition-all ${
              toast.type === "error"
                ? "bg-red-50 text-red-700 border border-red-200"
                : "bg-green-50 text-green-700 border border-green-200"
            }`}
          >
            {toast.message}
          </div>
        )}

        <div className="grid gap-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <p className="text-sm text-slate-600">
              Provide project details manually, upload client documents, or both.
            </p>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <h2 className="text-lg font-semibold text-slate-900 mb-4">Manual Details</h2>
                <div className="space-y-4">
                  <div>
                    <label
                      htmlFor="additional-details"
                      className="block text-sm font-medium text-slate-700 mb-2"
                    >
                      Additional Details
                    </label>
                    <textarea
                      id="additional-details"
                      value={additionalDetails}
                      onChange={(e) => setAdditionalDetails(e.target.value)}
                      placeholder="Describe your project in detail..."
                      className="text-black w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                      rows={8}
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
                        <label
                          key={option}
                          className="inline-flex items-center gap-2 cursor-pointer select-none"
                        >
                          <input
                            type="checkbox"
                            checked={buildOptions.includes(option)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setBuildOptions((prev) => [...prev, option]);
                              } else {
                                setBuildOptions((prev) => prev.filter((x) => x !== option));
                              }
                            }}
                            className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="text-sm text-slate-700">
                            {BUILD_OPTION_LABELS[option]}
                          </span>
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
                      Timeline Constraint
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
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <h2 className="text-lg font-semibold text-slate-900 mb-4">Document Upload</h2>
                <div
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    const dropped = e.dataTransfer.files?.[0] || null;
                    handleFileSelect(dropped);
                  }}
                  className="group rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 p-6 text-center transition-all hover:border-blue-400 hover:bg-blue-50"
                >
                  <input
                    id="doc-upload"
                    type="file"
                    accept=".pdf,.docx,.xlsx"
                    className="hidden"
                    onChange={(e) => handleFileSelect(e.target.files?.[0] || null)}
                  />
                  <label htmlFor="doc-upload" className="cursor-pointer">
                    <span className="inline-block rounded-md bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm">
                      Choose file or drag & drop
                    </span>
                  </label>
                  <p className="mt-3 text-xs text-slate-500">Supports PDF, DOCX, XLSX</p>

                  {selectedFile && (
                    <div className="mt-4 rounded-md border border-slate-200 bg-white px-3 py-2 text-left">
                      <p className="text-sm font-medium text-slate-800 truncate">{selectedFile.name}</p>
                      <p className="text-xs text-slate-500">
                        {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                      </p>
                      <button
                        type="button"
                        className="mt-2 text-xs text-red-600 hover:text-red-700"
                        onClick={() => setSelectedFile(null)}
                      >
                        Remove file
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              {loading ? "Generating Estimation..." : "Generate Estimation"}
            </button>
          </form>

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

              <PlanningBreakdown planning={results.planning} />

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
