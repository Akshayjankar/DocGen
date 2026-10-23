"use client";

import { contrastRatio, meetsAa } from "@/lib/color";
import { useThemeStore } from "@/lib/theme-store";

export function ContrastRing() {
  const brand = useThemeStore((s) => s.brandPrimary);
  const paper = "#F6F2EA";
  const ink = "#1A1714";
  const brandOnPaper = contrastRatio(brand, paper);
  const inkOnTint = contrastRatio(ink, "#E4F2ED");
  const brandAa = meetsAa(brand, paper, true);
  const textAa = meetsAa(ink, paper);

  const r = 36;
  const c = 2 * Math.PI * r;
  const score = Math.min(1, brandOnPaper / 7);
  const dash = c * score;

  return (
    <div className="flex items-center gap-4 rounded-[var(--radius-md)] border border-border bg-surface p-3">
      <svg width="88" height="88" viewBox="0 0 88 88" aria-hidden>
        <circle
          cx="44"
          cy="44"
          r={r}
          fill="none"
          stroke="var(--border)"
          strokeWidth="8"
        />
        <circle
          cx="44"
          cy="44"
          r={r}
          fill="none"
          stroke="var(--brand)"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${c - dash}`}
          transform="rotate(-90 44 44)"
        />
        <text
          x="44"
          y="48"
          textAnchor="middle"
          className="fill-[var(--fg)] font-mono text-[12px]"
        >
          {brandOnPaper.toFixed(1)}:1
        </text>
      </svg>
      <div className="space-y-1 text-sm">
        <p className="font-medium">Contrast</p>
        <p className={brandAa ? "text-success" : "text-warning"}>
          Brand on paper · {brandAa ? "AA large" : "Adjust"}
        </p>
        <p className={textAa ? "text-success" : "text-danger"}>
          Body text · {textAa ? "AA pass" : "Fail"}
        </p>
        <p className="font-mono text-[11px] text-fg-muted">
          Tint pair {inkOnTint.toFixed(1)}:1
        </p>
      </div>
    </div>
  );
}
