"use client";

import { create } from "zustand";
import { brandToCssVars, deriveBrandTint, type Hex } from "@/lib/color";
import type { Theme } from "@/types/api";

const DEFAULT_PRIMARY = "#1F6F5B" as Hex;

interface ThemeState {
  brandPrimary: Hex;
  theme: Theme | null;
  logoPreviewUrl: string | null;
  logoFileName: string | null;
  setBrandPrimary: (hex: string) => void;
  setThemeFromApi: (theme: Theme, logoUrl?: string | null) => void;
  clearBrand: () => void;
  applyCssVars: () => void;
}

function applyVars(primary: string) {
  if (typeof document === "undefined") return;
  const vars = brandToCssVars(primary);
  const root = document.documentElement;
  for (const [k, v] of Object.entries(vars)) {
    root.style.setProperty(k, v);
  }
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  brandPrimary: DEFAULT_PRIMARY,
  theme: null,
  logoPreviewUrl: null,
  logoFileName: null,

  setBrandPrimary: (hex) => {
    const primary = hex.toUpperCase() as Hex;
    const tint = deriveBrandTint(primary);
    const prev = get().theme;
    const theme = prev
      ? {
          ...prev,
          palette: {
            ...prev.palette,
            primary,
            primary_dark: tint.primaryDark,
            primary_tint: tint.primaryTint,
          },
          border: { ...prev.border, color: primary },
          source: "manual" as const,
        }
      : null;
    set({ brandPrimary: primary, ...(theme ? { theme } : {}) });
    applyVars(primary);
  },

  setThemeFromApi: (theme, logoUrl) => {
    const primary = theme.palette.primary.toUpperCase() as Hex;
    set({
      theme,
      brandPrimary: primary,
      logoPreviewUrl: logoUrl ?? get().logoPreviewUrl,
      logoFileName: theme.name,
    });
    applyVars(primary);
  },

  clearBrand: () => {
    set({
      brandPrimary: DEFAULT_PRIMARY,
      theme: null,
      logoPreviewUrl: null,
      logoFileName: null,
    });
    applyVars(DEFAULT_PRIMARY);
  },

  applyCssVars: () => applyVars(get().brandPrimary),
}));

export function getDefaultTint() {
  return deriveBrandTint(DEFAULT_PRIMARY);
}
