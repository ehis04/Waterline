"use client";

import { useState } from "react";

export interface DepthToggleProps {
  initialDepth?: number;
  onChange: (depth: number) => void;
}

const DEPTH_OPTIONS = [
  { value: 1, label: "1" },
  { value: 2, label: "2" },
  { value: 3, label: "3+" },
] as const;

export function DepthToggle({ initialDepth = 1, onChange }: DepthToggleProps) {
  const [selectedDepth, setSelectedDepth] = useState<number>(initialDepth);

  const handleSelect = (depth: number) => {
    setSelectedDepth(depth);
    onChange(depth);
  };

  return (
    <div
      role="group"
      aria-label="Depth selector"
      className="inline-flex items-center rounded-lg border border-slate-700 bg-slate-800 p-0.5"
    >
      {DEPTH_OPTIONS.map((option) => {
        const isActive = selectedDepth === option.value;
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={isActive}
            onClick={() => handleSelect(option.value)}
            className={`rounded-md px-3 py-1 text-xs font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 ${
              isActive
                ? "bg-emerald-500 text-slate-950"
                : "text-slate-300 hover:text-white"
            }`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
