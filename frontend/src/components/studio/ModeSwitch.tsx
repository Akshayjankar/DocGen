"use client";

import { Info, Lock, MagicWand } from "@phosphor-icons/react";
import { useStudioStore } from "@/lib/studio-store";
import { cn } from "@/lib/cn";

const MODE_HELP = {
  format_only: {
    label: "Format",
    title: "Format — keep your wording",
    blurb:
      "Locks every word you wrote. Docgen only structures and brands the document — tables, headings, and sentences stay exactly as pasted.",
  },
  improve: {
    label: "Improve",
    title: "Improve — suggest edits",
    blurb:
      "May rewrite for clarity. Each change shows as a diff you accept or reject before export. Use when you want editorial help.",
  },
} as const;

export function ModeSwitch({
  compact = true,
  className,
}: {
  compact?: boolean;
  className?: string;
}) {
  const mode = useStudioStore((s) => s.mode);
  const setMode = useStudioStore((s) => s.setMode);
  const help = MODE_HELP[mode];

  if (compact) {
    return (
      <div className={cn("flex max-w-xl flex-col gap-1", className)}>
        <div
          role="group"
          aria-label="Generation mode"
          className="inline-flex h-9 w-fit rounded-[var(--radius-md)] border border-border bg-surface p-0.5"
        >
          <button
            type="button"
            onClick={() => setMode("format_only")}
            title={MODE_HELP.format_only.title}
            aria-pressed={mode === "format_only"}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-[calc(var(--radius-md)-2px)] px-2.5 text-xs font-medium transition-colors",
              mode === "format_only"
                ? "bg-brand-tint text-brand"
                : "text-fg-muted hover:text-fg",
            )}
          >
            <Lock size={14} weight="duotone" />
            Format
          </button>
          <button
            type="button"
            onClick={() => setMode("improve")}
            title={MODE_HELP.improve.title}
            aria-pressed={mode === "improve"}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-[calc(var(--radius-md)-2px)] px-2.5 text-xs font-medium transition-colors",
              mode === "improve"
                ? "bg-brand-tint text-brand"
                : "text-fg-muted hover:text-fg",
            )}
          >
            <MagicWand size={14} weight="duotone" />
            Improve
          </button>
        </div>
        <p className="flex items-start gap-1 text-[11px] leading-snug text-fg-muted">
          <Info size={12} className="mt-0.5 shrink-0" aria-hidden />
          <span>
            <span className="font-medium text-fg">{help.label}:</span> {help.blurb}
          </span>
        </p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-2", className)}>
      <p className="text-xs font-medium uppercase tracking-wider text-fg-muted">Mode</p>
      <div className="grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={() => setMode("format_only")}
          aria-pressed={mode === "format_only"}
          className={cn(
            "flex flex-col gap-1 rounded-[var(--radius-md)] border px-3 py-3 text-left",
            mode === "format_only"
              ? "border-brand bg-brand-tint"
              : "border-border bg-surface",
          )}
        >
          <Lock size={18} className="text-brand" weight="duotone" />
          <span className="text-sm font-medium">Format</span>
          <span className="text-[11px] text-fg-muted">
            Your wording stays locked. Structure and brand only — best for SOPs and
            compliance.
          </span>
        </button>
        <button
          type="button"
          onClick={() => setMode("improve")}
          aria-pressed={mode === "improve"}
          className={cn(
            "flex flex-col gap-1 rounded-[var(--radius-md)] border px-3 py-3 text-left",
            mode === "improve"
              ? "border-brand bg-brand-tint"
              : "border-border bg-surface",
          )}
        >
          <MagicWand size={18} className="text-brand-accent" weight="duotone" />
          <span className="text-sm font-medium">Improve</span>
          <span className="text-[11px] text-fg-muted">
            Suggests clearer wording. Review each change and accept or reject before
            export.
          </span>
        </button>
      </div>
    </div>
  );
}
