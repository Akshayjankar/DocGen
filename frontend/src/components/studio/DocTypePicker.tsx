"use client";

import type { DocType } from "@/types/api";
import { useStudioStore } from "@/lib/studio-store";
import { cn } from "@/lib/cn";

import { FORMAT_OPTIONS } from "@/lib/format-options";

const types = FORMAT_OPTIONS;

export function DocTypePicker({
  compact = true,
  className,
}: {
  compact?: boolean;
  className?: string;
}) {
  const docType = useStudioStore((s) => s.docType);
  const setDocType = useStudioStore((s) => s.setDocType);
  const setFormatId = useStudioStore((s) => s.setFormatId);

  const pick = (id: DocType) => {
    setDocType(id);
    setFormatId(id);
  };

  if (compact) {
    return (
      <label className={cn("flex items-center gap-2 text-sm", className)}>
        <span className="sr-only">Document type</span>
        <select
          value={docType}
          onChange={(e) => pick(e.target.value as DocType)}
          aria-label="Document type"
          className="h-9 rounded-[var(--radius-md)] border border-border bg-surface px-2.5 text-sm outline-none focus:border-brand"
        >
          {types.map((t) => (
            <option key={t.id} value={t.id}>
              {t.label}
            </option>
          ))}
        </select>
      </label>
    );
  }

  return (
    <fieldset className={className}>
      <legend className="mb-2 text-xs font-medium uppercase tracking-wider text-fg-muted">
        Document type
      </legend>
      <div className="grid grid-cols-2 gap-2">
        {types.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => pick(t.id)}
            className={cn(
              "rounded-[var(--radius-md)] border px-3 py-2 text-left text-sm transition-colors",
              docType === t.id
                ? "border-brand bg-brand-tint font-medium"
                : "border-border bg-surface hover:bg-surface-2",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>
    </fieldset>
  );
}
