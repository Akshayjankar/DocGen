"use client";

import { FileText } from "@phosphor-icons/react";
import { useStudioStore } from "@/lib/studio-store";
import { cn } from "@/lib/cn";

export function TextInput({ className }: { className?: string }) {
  const text = useStudioStore((s) => s.text);
  const setText = useStudioStore((s) => s.setText);

  return (
    <div className={cn("flex h-full min-h-[22rem] flex-col gap-2.5 sm:min-h-[28rem]", className)}>
      <div className="flex shrink-0 items-center justify-between gap-2">
        <div>
          <label
            htmlFor="doc-text"
            className="font-display text-lg font-semibold tracking-tight"
          >
            Your notes
          </label>
          <p className="text-[11px] text-fg-muted">Paste, type, or upload — Format-only keeps every word.</p>
        </div>
        <label className="inline-flex cursor-pointer items-center gap-1.5 rounded-[var(--radius-sm)] border border-border bg-surface px-2.5 py-1.5 text-xs font-medium text-brand transition-colors hover:border-brand/40 hover:bg-brand-tint">
          <FileText size={14} />
          Upload
          <input
            type="file"
            accept=".txt,.md,.csv,text/plain,text/markdown,text/csv"
            className="sr-only"
            onChange={async (e) => {
              const f = e.target.files?.[0];
              if (!f) return;
              setText(await f.text());
            }}
          />
        </label>
      </div>
      <textarea
        id="doc-text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={
          "Paste or type your rough notes here…\n\n# Heading\n1. Step one\n- bullet\n\nNote: callouts work too"
        }
        className="panel-inset min-h-[18rem] flex-1 resize-y p-4 font-mono text-base leading-relaxed outline-none placeholder:text-fg-muted/65 focus:border-brand focus:ring-2 focus:ring-brand/20 sm:min-h-[24rem]"
      />
      <p className="shrink-0 font-mono text-[11px] text-fg-muted">
        {text.length.toLocaleString()} chars
        {text.trim() ? "" : " · this is where your wording goes"}
      </p>
    </div>
  );
}
