"use client";

import type { CornerAnchor, CornerPages } from "@/lib/studio-store";
import { useStudioStore } from "@/lib/studio-store";
import { cn } from "@/lib/cn";

function Segmented<T extends string>({
  label,
  value,
  options,
  onChange,
  disabled,
}: {
  label: string;
  value: T;
  options: { id: T; label: string }[];
  onChange: (v: T) => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[10px] font-medium uppercase tracking-wider text-fg-muted">
        {label}
      </span>
      <span
        role="group"
        aria-label={label}
        className={cn(
          "inline-flex overflow-hidden rounded-[var(--radius-sm)] border border-border",
          disabled && "opacity-50",
        )}
      >
        {options.map((opt) => (
          <button
            key={opt.id}
            type="button"
            disabled={disabled}
            aria-pressed={value === opt.id}
            onClick={() => onChange(opt.id)}
            className={cn(
              "px-2 py-1 text-[11px] transition-colors",
              value === opt.id
                ? "bg-brand-tint text-brand"
                : "bg-surface hover:bg-surface-2 hover:text-fg",
            )}
          >
            {opt.label}
          </button>
        ))}
      </span>
    </div>
  );
}

function HeaderDiagram({
  anchor,
  side,
  pages,
}: {
  anchor: CornerAnchor;
  side: "left" | "right";
  pages: CornerPages;
}) {
  const showLogo = pages !== "none";
  const x = side === "left" ? 6 : 54;
  const logoY = anchor === "corner" ? 4 : 10;
  const logoW = anchor === "corner" ? 10 : 8;
  const logoH = anchor === "corner" ? 6 : 5;
  return (
    <svg
      viewBox="0 0 64 28"
      className="h-7 w-16 shrink-0 rounded border border-border bg-surface-2"
      aria-hidden
    >
      <rect x="1" y="1" width="62" height="26" fill="var(--surface)" stroke="var(--border)" />
      <line x1="4" y1="18" x2="60" y2="18" stroke="var(--border)" strokeWidth="0.5" />
      {showLogo ? (
        <rect
          x={x}
          y={logoY}
          width={logoW}
          height={logoH}
          rx="1"
          fill="color-mix(in srgb, var(--brand) 55%, transparent)"
        />
      ) : null}
      <line x1="4" y1="22" x2="40" y2="22" stroke="var(--fg-muted)" strokeWidth="1" opacity="0.35" />
    </svg>
  );
}

export function CornerPlacementControl({ disabled }: { disabled?: boolean }) {
  const cornerAnchor = useStudioStore((s) => s.cornerAnchor);
  const cornerPosition = useStudioStore((s) => s.cornerPosition);
  const cornerPages = useStudioStore((s) => s.cornerPages);
  const cornerHeightMm = useStudioStore((s) => s.cornerHeightMm);
  const setLogoFlags = useStudioStore((s) => s.setLogoFlags);

  return (
    <div className="flex flex-col gap-2.5 rounded-[var(--radius-md)] border border-border bg-surface/80 p-2.5">
      <div className="flex items-start justify-between gap-2">
        <p className="text-xs font-medium text-fg">Corner placement</p>
        <HeaderDiagram
          anchor={cornerAnchor}
          side={cornerPosition}
          pages={cornerPages}
        />
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        <Segmented
          label="Anchor"
          value={cornerAnchor}
          disabled={disabled}
          onChange={(v) => setLogoFlags({ cornerAnchor: v })}
          options={[
            { id: "corner", label: "Hug corner" },
            { id: "margin", label: "Align with text" },
          ]}
        />
        <Segmented
          label="Side"
          value={cornerPosition}
          disabled={disabled}
          onChange={(v) => setLogoFlags({ cornerPosition: v })}
          options={[
            { id: "left", label: "Left" },
            { id: "right", label: "Right" },
          ]}
        />
      </div>

      <Segmented
        label="Show on"
        value={cornerPages}
        disabled={disabled}
        onChange={(v) => setLogoFlags({ cornerPages: v })}
        options={[
          { id: "all_except_cover", label: "Body pages" },
          { id: "all", label: "All pages" },
          { id: "none", label: "Hide" },
        ]}
      />

      <label className="flex flex-col gap-1">
        <span className="flex items-center justify-between text-[10px] font-medium uppercase tracking-wider text-fg-muted">
          Logo height
          <span className="font-mono normal-case text-fg">{cornerHeightMm} mm</span>
        </span>
        <input
          type="range"
          min={6}
          max={16}
          step={1}
          disabled={disabled}
          value={cornerHeightMm}
          onChange={(e) =>
            setLogoFlags({ cornerHeightMm: Number(e.target.value) })
          }
          className="accent-[var(--brand)]"
          aria-label="Corner logo height in millimeters"
        />
      </label>
    </div>
  );
}
