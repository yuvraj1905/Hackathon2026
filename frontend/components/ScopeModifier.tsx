"use client";

import { useState } from "react";

interface ScopeModifierProps {
  onModify: (instruction: string) => void;
  loading: boolean;
}

export function ScopeModifier({ onModify, loading }: ScopeModifierProps) {
  const [instruction, setInstruction] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (instruction.trim().length < 3) {
      alert("Please provide a modification instruction");
      return;
    }

    onModify(instruction);
    setInstruction("");
  };

  const quickActions = [
    "Add analytics dashboard",
    "Add social media login",
    "Remove review system",
    "Add mobile app support",
  ];

  return (
    <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border-2 border-indigo-200 rounded-lg p-5">
      <div className="flex items-center gap-2 mb-3">
        <svg
          className="w-5 h-5 text-indigo-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 10V3L4 14h7v7l9-11h-7z"
          />
        </svg>
        <h3 className="text-lg font-semibold text-slate-900">
          AI Scope Assistant
        </h3>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder="Modify scope (e.g., Add mobile app, Remove admin panel)"
            className="text-black flex-1 px-4 py-2.5 border border-indigo-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-white text-sm"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || instruction.trim().length < 3}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-400 text-white font-medium py-2.5 px-6 rounded-lg transition-colors text-sm whitespace-nowrap"
          >
            {loading ? "Applying..." : "Apply Changes"}
          </button>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-600">Quick actions:</span>
          <div className="flex flex-wrap gap-1.5">
            {quickActions.map((action, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setInstruction(action)}
                disabled={loading}
                className="text-xs bg-white hover:bg-indigo-50 disabled:bg-slate-50 text-slate-700 border border-indigo-200 px-2.5 py-1 rounded-md transition-colors"
              >
                {action}
              </button>
            ))}
          </div>
        </div>
      </form>
    </div>
  );
}
