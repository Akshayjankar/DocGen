"use client";

import type { JobStatus } from "@/types/api";
import { cn } from "@/lib/cn";

const stages: { id: JobStatus; label: string }[] = [
  { id: "queued", label: "Queued" },
  { id: "theme", label: "Theme" },
  { id: "ingest", label: "Ingest" },
  { id: "structure", label: "Structure" },
  { id: "verify", label: "Verify" },
  { id: "render_docx", label: "DOCX" },
  { id: "render_pdf", label: "PDF" },
  { id: "done", label: "Done" },
];

function stageIndex(status: JobStatus | null): number {
  if (!status || status === "failed") return -1;
  return stages.findIndex((s) => s.id === status);
}

export function PressProgress({
  status,
  progress,
  message,
}: {
  status: JobStatus | null;
  progress: number;
  message: string;
}) {
  const idx = stageIndex(status);
  const failed = status === "failed";

  return (
    <div className="space-y-3 rounded-[var(--radius-md)] border border-border bg-surface p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="font-display text-sm font-semibold">Press progress</p>
        <span className="font-mono text-xs text-fg-muted">
          {Math.round(progress * (progress <= 1 ? 100 : 1))}%
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-surface-2">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-500",
            failed ? "bg-danger" : "bg-brand",
          )}
          style={{
            width: `${Math.min(100, progress <= 1 ? progress * 100 : progress)}%`,
          }}
        />
      </div>
      <ol className="grid grid-cols-4 gap-2 sm:grid-cols-8">
        {stages.map((s, i) => {
          const done = idx > i || status === "done";
          const current = idx === i;
          return (
            <li
              key={s.id}
              className={cn(
                "rounded-[var(--radius-sm)] px-1 py-1.5 text-center font-mono text-[10px]",
                done && "bg-brand-tint text-brand-dark",
                current && !done && "bg-brand text-white",
                !done && !current && "bg-surface-2 text-fg-muted",
              )}
            >
              {s.label}
            </li>
          );
        })}
      </ol>
      <p className="text-xs text-fg-muted">{message || "Waiting for the press…"}</p>
    </div>
  );
}
