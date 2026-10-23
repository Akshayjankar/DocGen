"use client";

import { Warning, Info, XCircle } from "@phosphor-icons/react";
import type { LintItem } from "@/types/api";
import { cn } from "@/lib/cn";

const icons = {
  info: Info,
  warning: Warning,
  error: XCircle,
};

function lintLevel(item: LintItem): "info" | "warning" | "error" {
  return item.level ?? item.severity ?? "info";
}

export function LintPanel({ items }: { items: LintItem[] }) {
  if (items.length === 0) {
    return (
      <p className="rounded-[var(--radius-md)] border border-dashed border-border p-4 text-sm text-fg-muted">
        Lint is quiet — run a job to see accessibility and structure checks.
      </p>
    );
  }

  return (
    <ul className="space-y-2">
      {items.map((item, i) => {
        const level = lintLevel(item);
        const Icon = icons[level];
        return (
          <li
            key={`${item.code}-${i}`}
            className={cn(
              "flex gap-3 rounded-[var(--radius-md)] border px-3 py-2.5 text-sm",
              level === "error" && "border-danger/30 bg-[color-mix(in_srgb,var(--danger)_8%,var(--surface))]",
              level === "warning" && "border-warning/30 bg-[color-mix(in_srgb,var(--warning)_8%,var(--surface))]",
              level === "info" && "border-border bg-surface",
            )}
          >
            <Icon
              size={18}
              className={cn(
                "mt-0.5 shrink-0",
                level === "error" && "text-danger",
                level === "warning" && "text-warning",
                level === "info" && "text-info",
              )}
            />
            <div>
              <p className="font-mono text-[11px] text-fg-muted">{item.code}</p>
              <p>{item.message}</p>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
