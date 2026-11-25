"use client";

import { useState } from "react";

export interface ReceiptChipProps {
  hash: string;
}

export function ReceiptChip({ hash }: ReceiptChipProps) {
  const [copied, setCopied] = useState(false);
  const shortHash = hash.slice(0, 8);

  const handleCopy = async () => {
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(hash);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard write may fail in restricted contexts
    }
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      aria-label={`Receipt hash ${hash}`}
      title={copied ? "Copied!" : `Copy full hash: ${hash}`}
      className="inline-flex items-center gap-1.5 rounded-full border border-slate-700 bg-slate-800 px-3 py-1 text-xs font-mono text-emerald-400 transition-colors hover:border-emerald-500/60 hover:bg-slate-700/80 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
    >
      <svg
        aria-hidden="true"
        className="h-3.5 w-3.5 shrink-0 text-emerald-500"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
      <span>{copied ? "Copied" : shortHash}</span>
    </button>
  );
}
