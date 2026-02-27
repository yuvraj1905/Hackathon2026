"use client";

interface ProgressIndicatorProps {
  stage: string;
  data?: {
    domain?: string;
    confidence?: number;
    feature_count?: number;
    total_hours?: number;
  };
}

const STEPS = [
  { key: "domain_detection", label: "Detecting Domain" },
  { key: "feature_structuring", label: "Structuring Features" },
  { key: "estimation", label: "Calculating Estimates" },
  { key: "proposal", label: "Generating Proposal" },
];

export function ProgressIndicator({ stage, data }: ProgressIndicatorProps) {
  const getCurrentStepIndex = () => {
    if (stage.includes("domain_detection")) return 0;
    if (stage.includes("feature_structuring")) return 1;
    if (stage.includes("estimation")) return 2;
    if (stage.includes("proposal") || stage === "completed") return 3;
    return -1;
  };

  const currentStepIndex = getCurrentStepIndex();
  const isCompleted = stage === "completed";

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-slate-900">
          {isCompleted ? "Estimation Complete" : "Processing Estimation"}
        </h3>
        {!isCompleted && (
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <div className="animate-pulse w-2 h-2 bg-blue-600 rounded-full"></div>
            <span>In progress</span>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between mb-6">
        {STEPS.map((step, index) => {
          const isActive = index === currentStepIndex;
          const isDone = index < currentStepIndex || isCompleted;
          const isCurrent = index === currentStepIndex && !isCompleted;

          return (
            <div key={step.key} className="flex items-center flex-1">
              <div className="flex flex-col items-center flex-1">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 ${
                    isDone
                      ? "bg-green-500 text-white"
                      : isCurrent
                      ? "bg-blue-600 text-white animate-pulse"
                      : "bg-slate-200 text-slate-400"
                  }`}
                >
                  {isDone ? (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  ) : (
                    <span className="text-sm font-semibold">{index + 1}</span>
                  )}
                </div>
                <p
                  className={`mt-2 text-xs text-center transition-colors ${
                    isActive || isDone ? "text-slate-900 font-medium" : "text-slate-500"
                  }`}
                >
                  {step.label}
                </p>
              </div>
              {index < STEPS.length - 1 && (
                <div
                  className={`h-0.5 flex-1 mx-2 transition-all duration-300 ${
                    isDone ? "bg-green-500" : "bg-slate-200"
                  }`}
                ></div>
              )}
            </div>
          );
        })}
      </div>

      {data && (
        <div className="bg-slate-50 rounded-lg p-4 space-y-2 text-sm">
          {data.domain && (
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Domain:</span>
              <div className="flex items-center gap-2">
                <span className="font-medium text-slate-900 capitalize">{data.domain}</span>
                {data.confidence && (
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                    {Math.round(data.confidence * 100)}%
                  </span>
                )}
              </div>
            </div>
          )}
          {data.feature_count !== undefined && (
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Features:</span>
              <span className="font-medium text-slate-900">{data.feature_count}</span>
            </div>
          )}
          {data.total_hours !== undefined && (
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Total Hours:</span>
              <span className="font-medium text-slate-900">{data.total_hours}h</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

