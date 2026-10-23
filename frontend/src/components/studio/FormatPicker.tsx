"use client";

import type { DocType } from "@/types/api";
import { useStudioStore } from "@/lib/studio-store";
import { cn } from "@/lib/cn";
import { DocTypePicker } from "@/components/studio/DocTypePicker";
import { FORMAT_OPTIONS } from "@/lib/format-options";

export { FORMAT_OPTIONS };

function selectFormat(id: DocType) {
  const { setDocType, setFormatId } = useStudioStore.getState();
  setDocType(id);
  setFormatId(id);
}

export function FormatPicker({
  compact = true,
  className,
}: {
  compact?: boolean;
  className?: string;
}) {
  const docType = useStudioStore((s) => s.docType);
  const formatId = useStudioStore((s) => s.formatId);

  if (compact) {
    return <DocTypePicker compact className={className} />;
  }

  const active = formatId || docType;

  return (
    <fieldset className={className}>
      <legend className="mb-2 text-xs font-medium uppercase tracking-wider text-fg-muted">
        Format
      </legend>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {FORMAT_OPTIONS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => selectFormat(t.id)}
            className={cn(
              "rounded-[var(--radius-md)] border px-3 py-2 text-left transition-colors",
              active === t.id
                ? "border-brand bg-brand-tint font-medium"
                : "border-border bg-surface hover:bg-surface-2",
            )}
          >
            <span className="block text-sm">{t.label}</span>
            {t.hint ? (
              <span className="text-[10px] text-fg-muted">{t.hint}</span>
            ) : null}
          </button>
        ))}
      </div>
    </fieldset>
  );
}
