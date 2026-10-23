"use client";

import { Check, X } from "@phosphor-icons/react";
import { Button } from "@/components/ui/Button";
import { useStudioStore } from "@/lib/studio-store";

export function DiffReview() {
  const diffs = useStudioStore((s) => s.diffs);
  const acceptDiff = useStudioStore((s) => s.acceptDiff);
  const rejectDiff = useStudioStore((s) => s.rejectDiff);
  const mode = useStudioStore((s) => s.mode);

  if (mode !== "improve") {
    return (
      <p className="rounded-[var(--radius-md)] border border-border bg-surface p-4 text-sm text-fg-muted">
        Diff review appears in Improve mode after structuring.
      </p>
    );
  }

  if (diffs.length === 0) {
    return (
      <p className="rounded-[var(--radius-md)] border border-dashed border-border p-4 text-sm text-fg-muted">
        No diffs yet. Run the press to review block-level rewrites.
      </p>
    );
  }

  return (
    <ul className="space-y-3">
      {diffs.map((d) => (
        <li
          key={d.block_id}
          className="overflow-hidden rounded-[var(--radius-md)] border border-border bg-surface"
        >
          <div className="flex items-center justify-between border-b border-border px-3 py-2">
            <span className="font-mono text-[11px] text-fg-muted">{d.block_id}</span>
            <span className="flex gap-1">
              <Button
                size="sm"
                variant={d.accepted === true ? "primary" : "secondary"}
                onClick={() => acceptDiff(d.block_id)}
                aria-label="Accept rewrite"
              >
                <Check size={14} />
              </Button>
              <Button
                size="sm"
                variant={d.accepted === false ? "danger" : "secondary"}
                onClick={() => rejectDiff(d.block_id)}
                aria-label="Reject rewrite"
              >
                <X size={14} />
              </Button>
            </span>
          </div>
          <div className="grid gap-0 sm:grid-cols-2">
            <pre className="overflow-auto bg-[#1a1714] p-3 font-mono text-[11px] text-[#e8e0d4]">
              {d.before}
            </pre>
            <pre className="overflow-auto bg-brand-tint/40 p-3 font-mono text-[11px] text-fg">
              {d.after}
            </pre>
          </div>
        </li>
      ))}
    </ul>
  );
}
