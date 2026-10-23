"use client";

import { SealCheck } from "@phosphor-icons/react";
import { cn } from "@/lib/cn";

export function ContentSeal({
  preservedPct,
  mode,
}: {
  preservedPct: number | null;
  mode: "format_only" | "improve";
}) {
  const pct = preservedPct ?? (mode === "format_only" ? null : null);
  const locked = pct !== null && pct >= 99.5;

  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-[var(--radius-md)] border p-4",
        locked
          ? "border-success/40 bg-[color-mix(in_srgb,var(--success)_10%,var(--surface))]"
          : "border-border bg-surface",
      )}
    >
      <SealCheck
        size={36}
        weight="duotone"
        className={locked ? "text-success" : "text-fg-muted"}
      />
      <div>
        <p className="font-display text-sm font-semibold">Content Seal</p>
        {pct === null ? (
          <p className="text-xs text-fg-muted">
            {mode === "format_only"
              ? "Verifier will prove 100% span coverage after press."
              : "Improve mode emits diffs — seal reports accepted wording."}
          </p>
        ) : (
          <p className="font-mono text-sm">
            <span className={locked ? "text-success" : "text-warning"}>
              {pct.toFixed(1)}%
            </span>{" "}
            <span className="text-fg-muted">source preserved</span>
          </p>
        )}
      </div>
    </div>
  );
}
