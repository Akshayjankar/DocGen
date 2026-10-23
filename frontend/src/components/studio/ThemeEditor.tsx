"use client";

import { useThemeStore } from "@/lib/theme-store";
import { useStudioStore } from "@/lib/studio-store";
import { normalizeHex } from "@/lib/color";
import { applyBrandPrimary } from "@/lib/preview-theme";

export function ThemeEditor() {
  const brandPrimary = useThemeStore((s) => s.brandPrimary);
  const setBrandPrimary = useThemeStore((s) => s.setBrandPrimary);
  const theme = useStudioStore((s) => s.theme);
  const setTheme = useStudioStore((s) => s.setTheme);

  const onPrimary = (raw: string) => {
    try {
      const hex = normalizeHex(raw);
      setBrandPrimary(hex);
      if (theme) setTheme(applyBrandPrimary(theme, hex));
    } catch {
      /* wait for valid hex */
    }
  };

  return (
    <div className="space-y-3 rounded-[var(--radius-md)] border border-border bg-surface p-3">
      <p className="text-xs font-medium uppercase tracking-wider text-fg-muted">
        Theme
      </p>
      <label className="flex items-center justify-between gap-3 text-sm">
        <span>Primary</span>
        <span className="flex items-center gap-2">
          <input
            type="color"
            value={brandPrimary}
            onChange={(e) => onPrimary(e.target.value)}
            className="size-8 cursor-pointer rounded border border-border bg-transparent"
            aria-label="Brand primary color"
          />
          <input
            type="text"
            value={brandPrimary}
            onChange={(e) => onPrimary(e.target.value)}
            className="w-[7.5rem] rounded border border-border bg-bg px-2 py-1 font-mono text-xs"
          />
        </span>
      </label>
      <div className="flex gap-1.5">
        {[
          brandPrimary,
          "color-mix(in srgb, var(--brand) 55%, white)",
          "var(--brand-tint)",
          "var(--brand-accent)",
        ].map((c, i) => (
          <span
            key={i}
            className="h-8 flex-1 rounded-[var(--radius-sm)] border border-border"
            style={{ background: c }}
          />
        ))}
      </div>
      {theme ? (
        <p className="font-mono text-[11px] text-fg-muted">
          Source: {theme.source ?? "logo"} · {theme.fonts.heading} / {theme.fonts.body}
        </p>
      ) : (
        <p className="text-[11px] text-fg-muted">
          Drop a logo to extract a full Theme, or tint manually.
        </p>
      )}
    </div>
  );
}
