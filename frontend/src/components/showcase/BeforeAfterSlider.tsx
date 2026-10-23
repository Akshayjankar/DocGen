"use client";

import { useState } from "react";
import { Slider } from "@/components/ui/Slider";
import { cn } from "@/lib/cn";

export function BeforeAfterSlider({ className }: { className?: string }) {
  const [pos, setPos] = useState(52);

  return (
    <div className={cn("overflow-hidden rounded-[var(--radius-lg)] border border-border", className)}>
      <div className="relative aspect-[16/10] bg-surface-2">
        {/* After (branded) */}
        <div className="absolute inset-0 bg-[#fffdf8] p-6 sm:p-10">
          <div className="h-full rounded-sm border border-black/10 p-5 shadow-inner">
            <div className="mb-3 h-1 w-full bg-[var(--brand)]" />
            <p className="font-display text-lg font-semibold text-black/85">
              Incident Response SOP
            </p>
            <p className="mt-1 text-xs text-black/45">v1.2 · Internal · Page 1 of 12</p>
            <div className="mt-6 space-y-2">
              <div className="h-2 w-[70%] rounded bg-[var(--brand)]/70" />
              <div className="h-2 w-full rounded bg-black/8" />
              <div className="h-2 w-[88%] rounded bg-black/8" />
              <div className="mt-4 overflow-hidden rounded border border-black/10">
                <div className="grid grid-cols-3 bg-[var(--brand)] text-[10px] text-white">
                  <span className="px-2 py-1">Step</span>
                  <span className="px-2 py-1">Owner</span>
                  <span className="px-2 py-1">SLA</span>
                </div>
                {[1, 2, 3].map((r) => (
                  <div
                    key={r}
                    className={cn(
                      "grid grid-cols-3 text-[10px] text-black/70",
                      r % 2 === 0 ? "bg-[color-mix(in_srgb,var(--brand)_12%,white)]" : "bg-white",
                    )}
                  >
                    <span className="px-2 py-1">0{r}</span>
                    <span className="px-2 py-1">SecOps</span>
                    <span className="px-2 py-1">15m</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <span className="absolute top-3 right-3 rounded bg-brand px-2 py-0.5 font-mono text-[10px] text-white">
            AFTER
          </span>
        </div>

        {/* Before (raw) clipped */}
        <div
          className="absolute inset-0 overflow-hidden bg-[#1a1714]"
          style={{ width: `${pos}%` }}
        >
          <div className="h-full w-[100vw] max-w-[720px] p-6 font-mono text-[11px] leading-relaxed text-[#c8c2b6] sm:p-10">
            <p>## incident response</p>
            <p className="mt-2 opacity-70">todo: format this later</p>
            <p className="mt-4">1. detect</p>
            <p>2. contain??</p>
            <p>3. notify stakeholders</p>
            <p className="mt-4">| step | owner | sla |</p>
            <p>| 1 | secops | 15m |</p>
            <p className="mt-6 opacity-50">// pasted from slack · 2:14am</p>
          </div>
          <span className="absolute top-3 left-3 rounded bg-white/10 px-2 py-0.5 font-mono text-[10px] text-white">
            BEFORE
          </span>
        </div>

        <div
          className="absolute inset-y-0 z-10 w-0.5 bg-brand"
          style={{ left: `${pos}%` }}
          aria-hidden
        >
          <span className="absolute top-1/2 left-1/2 flex size-8 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border-2 border-brand bg-surface text-xs font-bold shadow">
            ⇆
          </span>
        </div>
      </div>
      <div className="border-t border-border bg-surface px-4 py-3">
        <Slider
          value={pos}
          onChange={setPos}
          label="Reveal branded output"
          min={8}
          max={92}
        />
      </div>
    </div>
  );
}
