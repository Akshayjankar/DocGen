"use client";

import { useThemeStore } from "@/lib/theme-store";
import { cn } from "@/lib/cn";

const presets = [
  { name: "Evergreen", primary: "#1F6F5B" },
  { name: "Harbor", primary: "#1B4F72" },
  { name: "Copper", primary: "#9A3412" },
  { name: "Ink Oak", primary: "#5C4033" },
  { name: "Signal", primary: "#B45309" },
  { name: "Teal Press", primary: "#0F766E" },
];

export function BrandGallery({ className }: { className?: string }) {
  const setBrandPrimary = useThemeStore((s) => s.setBrandPrimary);
  const brandPrimary = useThemeStore((s) => s.brandPrimary);

  return (
    <div className={cn("grid gap-3 sm:grid-cols-2 lg:grid-cols-3", className)}>
      {presets.map((p) => {
        const active = brandPrimary.toUpperCase() === p.primary.toUpperCase();
        return (
          <button
            key={p.name}
            type="button"
            onClick={() => setBrandPrimary(p.primary)}
            className={cn(
              "group overflow-hidden rounded-[var(--radius-md)] border text-left transition-all",
              active
                ? "border-brand ring-2 ring-brand/30"
                : "border-border hover:border-brand/50",
            )}
          >
            <div
              className="h-16"
              style={{
                background: `linear-gradient(135deg, ${p.primary}, color-mix(in srgb, ${p.primary} 40%, #1a1714))`,
              }}
            />
            <div className="flex items-center justify-between bg-surface px-3 py-2.5">
              <span className="text-sm font-medium">{p.name}</span>
              <span className="font-mono text-[10px] text-fg-muted">{p.primary}</span>
            </div>
          </button>
        );
      })}
    </div>
  );
}
