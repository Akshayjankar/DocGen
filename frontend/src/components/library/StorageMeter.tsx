"use client";

import { LIBRARY_MAX_BYTES } from "@/lib/library-db";
import { cn } from "@/lib/cn";

export function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export function StorageMeter({
  bytes,
  count,
  className,
}: {
  bytes: number;
  count: number;
  className?: string;
}) {
  const pct = Math.min(100, (bytes / LIBRARY_MAX_BYTES) * 100);
  return (
    <div className={cn("min-w-[12rem]", className)}>
      <div className="flex items-baseline justify-between gap-3 font-mono text-[11px] text-fg-muted">
        <span>
          {count} {count === 1 ? "document" : "documents"}
        </span>
        <span>
          {formatBytes(bytes)} / {formatBytes(LIBRARY_MAX_BYTES)}
        </span>
      </div>
      <div
        role="progressbar"
        aria-label="Library storage used"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(pct)}
        className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-surface-2"
      >
        <div
          className={cn("h-full rounded-full", pct > 85 ? "bg-warning" : "bg-brand")}
          style={{ width: `${Math.max(pct, bytes > 0 ? 2 : 0)}%` }}
        />
      </div>
    </div>
  );
}
