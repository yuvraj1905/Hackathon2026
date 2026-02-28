"use client";

import React from "react";
import { fmtNum } from "@/lib/utils";

export interface EditableCellProps {
  value: number;
  onChange: (v: number) => void;
}

export const EditableCell = ({ value, onChange }: EditableCellProps) => {
  const [editing, setEditing] = React.useState(false);
  const [val, setVal] = React.useState(String(value));

  const commit = React.useCallback(
    (v: string) => {
      const n = parseFloat(v);
      onChange(Number.isNaN(n) ? 0 : Math.round(n * 100) / 100);
      setEditing(false);
    },
    [onChange],
  );

  if (editing) {
    return (
      <input
        type="number"
        autoFocus
        className="h-7 w-16 rounded-lg border border-primary/50 bg-background/80 text-center text-sm font-medium shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
        value={val}
        onChange={(e) => setVal(e.target.value)}
        onBlur={() => commit(val)}
        onKeyDown={(e) => {
          if (e.key === "Enter") commit(val);
          if (e.key === "Escape") setEditing(false);
        }}
      />
    );
  }

  return (
    <span
      className="inline-block min-w-[2.5rem] cursor-pointer rounded-lg px-2 py-1 text-center text-sm font-medium font-mono transition-all duration-200 hover:bg-primary/8 hover:text-primary"
      onClick={() => {
        setVal(String(value));
        setEditing(true);
      }}
      title="Click to edit"
    >
      {fmtNum(value)}
    </span>
  );
};

export interface EditableNameCellProps {
  value: string;
  onChange: (v: string) => void;
  className?: string;
}

export const EditableNameCell = ({ value, onChange, className = "" }: EditableNameCellProps) => {
  const [editing, setEditing] = React.useState(false);
  const [val, setVal] = React.useState(value);

  const commit = React.useCallback(
    (v: string) => {
      onChange(v);
      setEditing(false);
    },
    [onChange],
  );

  if (editing) {
    return (
      <input
        type="text"
        autoFocus
        className={`h-7 w-full max-w-[260px] rounded-lg border border-primary/50 bg-background/80 px-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/30 ${className}`}
        value={val}
        onChange={(e) => setVal(e.target.value)}
        onBlur={() => commit(val)}
        onKeyDown={(e) => {
          if (e.key === "Enter") commit(val);
          if (e.key === "Escape") setEditing(false);
        }}
      />
    );
  }

  return (
    <span
      className={`cursor-pointer rounded-lg px-1.5 py-0.5 text-sm transition-all duration-200 hover:bg-primary/8 hover:text-primary ${className}`}
      onClick={() => {
        setVal(value);
        setEditing(true);
      }}
      title="Click to edit"
    >
      {value}
    </span>
  );
};
