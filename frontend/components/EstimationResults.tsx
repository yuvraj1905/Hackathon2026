"use client";

interface EstimationResultsProps {
  data: any;
}

export function EstimationResults({ data }: EstimationResultsProps) {
  const { domain_detection, estimation, tech_stack, proposal } = data;

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-semibold text-slate-900 mb-6">
          Estimation Results
        </h2>

        <div className="space-y-6">
          <div className="border-b border-slate-200 pb-4">
            <h3 className="text-lg font-semibold text-slate-800 mb-2">
              Domain Detection
            </h3>
            <div className="flex items-center justify-between">
              <span className="text-slate-600">
                Detected Domain:{" "}
                <span className="font-medium text-slate-900 capitalize">
                  {domain_detection.detected_domain}
                </span>
              </span>
              <span className="text-sm bg-blue-100 text-blue-800 px-3 py-1 rounded-full">
                {Math.round(domain_detection.confidence * 100)}% confidence
              </span>
            </div>
            <p className="text-sm text-slate-600 mt-2">
              {domain_detection.reasoning}
            </p>
          </div>

          <div className="border-b border-slate-200 pb-4">
            <h3 className="text-lg font-semibold text-slate-800 mb-3">
              Estimation Summary
            </h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-slate-50 p-4 rounded-lg">
                <p className="text-sm text-slate-600 mb-1">Total Hours</p>
                <p className="text-2xl font-bold text-slate-900">
                  {estimation.total_hours}
                </p>
              </div>
              <div className="bg-slate-50 p-4 rounded-lg">
                <p className="text-sm text-slate-600 mb-1">Min - Max</p>
                <p className="text-lg font-semibold text-slate-900">
                  {estimation.min_hours} - {estimation.max_hours}
                </p>
              </div>
              <div className="bg-slate-50 p-4 rounded-lg">
                <p className="text-sm text-slate-600 mb-1">Confidence</p>
                <p className="text-2xl font-bold text-slate-900">
                  {Math.round(estimation.confidence_score * 100)}%
                </p>
              </div>
            </div>
            <p className="text-sm text-slate-600 mt-3">
              Complexity:{" "}
              <span className="font-medium capitalize">
                {estimation.overall_complexity.replace("_", " ")}
              </span>
            </p>
          </div>

          <div className="border-b border-slate-200 pb-4">
            <h3 className="text-lg font-semibold text-slate-800 mb-3">
              Tech Stack
            </h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="font-medium text-slate-700 mb-1">Frontend</p>
                <p className="text-slate-600">
                  {tech_stack.frontend.join(", ")}
                </p>
              </div>
              <div>
                <p className="font-medium text-slate-700 mb-1">Backend</p>
                <p className="text-slate-600">
                  {tech_stack.backend.join(", ")}
                </p>
              </div>
              <div>
                <p className="font-medium text-slate-700 mb-1">Database</p>
                <p className="text-slate-600">
                  {tech_stack.database.join(", ")}
                </p>
              </div>
              <div>
                <p className="font-medium text-slate-700 mb-1">Infrastructure</p>
                <p className="text-slate-600">
                  {tech_stack.infrastructure.join(", ")}
                </p>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-slate-800 mb-3">
              Proposal Summary
            </h3>
            <div className="space-y-3 text-sm">
              <div>
                <p className="font-medium text-slate-700 mb-1">
                  Executive Summary
                </p>
                <p className="text-slate-600">{proposal.executive_summary}</p>
              </div>
              <div>
                <p className="font-medium text-slate-700 mb-1">Timeline</p>
                <p className="text-slate-600">
                  {proposal.timeline_weeks} weeks
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-xl font-semibold text-slate-900 mb-4">
          Feature Breakdown
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
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
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {estimation.features.map((feature: any, idx: number) => (
                <tr key={idx} className="hover:bg-slate-50">
                  <td className="px-4 py-3 text-slate-900">{feature.name}</td>
                  <td className="px-4 py-3 text-slate-600">
                    {feature.description}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                        feature.complexity === "low"
                          ? "bg-green-100 text-green-800"
                          : feature.complexity === "medium"
                          ? "bg-yellow-100 text-yellow-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {feature.complexity}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-medium text-slate-900">
                    {feature.estimated_hours}h
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
