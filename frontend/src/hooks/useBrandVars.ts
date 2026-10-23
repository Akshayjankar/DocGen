"use client";

import { useEffect } from "react";
import { ambientToCssVars, brandToCssVars } from "@/lib/color";
import { useStudioStore } from "@/lib/studio-store";
import { useThemeStore } from "@/lib/theme-store";

function applyAmbientVars(primary: string, secondary?: string, accent?: string) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  for (const [k, v] of Object.entries(ambientToCssVars(primary, secondary, accent))) {
    root.style.setProperty(k, v);
  }
}

/** Keep CSS brand + ambient variables synced with theme / studio palette. */
export function useBrandVars(): string {
  const brandPrimary = useThemeStore((s) => s.brandPrimary);
  const storeTheme = useThemeStore((s) => s.theme);
  const studioTheme = useStudioStore((s) => s.theme);
  const applyCssVars = useThemeStore((s) => s.applyCssVars);

  useEffect(() => {
    applyCssVars();
    const palette = studioTheme?.palette ?? storeTheme?.palette;
    const primary = palette?.primary ?? brandPrimary;
    applyAmbientVars(
      primary,
      palette?.secondary,
      palette?.accent ?? palette?.primary_tint,
    );
  }, [brandPrimary, storeTheme, studioTheme, applyCssVars]);

  return brandPrimary;
}
