import { deriveBrandTint } from "@/lib/color";
import type { LogoSet, Theme } from "@/types/api";

export const DEFAULT_BRAND = "#1F6F5B";

/** Patch palette + border so Brand & checks primary wins over logo extraction. */
export function applyBrandPrimary(theme: Theme, brandPrimary: string): Theme {
  const primary = brandPrimary.toUpperCase();
  const tint = deriveBrandTint(primary);
  return {
    ...theme,
    palette: {
      ...theme.palette,
      primary,
      primary_dark: tint.primaryDark,
      primary_tint: tint.primaryTint,
    },
    border: { ...theme.border, color: primary },
    source: "manual",
  };
}

export interface PreviewThemeInput {
  /** Theme chosen in Studio (logo extraction / brand kit). */
  studioTheme: Theme | null;
  /** Theme from the landing Chroma Drop, if any. */
  storeTheme: Theme | null;
  /** Live brand primary (ThemeEditor may differ from the extracted theme). */
  brandPrimary: string;
  hasCover: boolean;
  flags: {
    sameForBoth: boolean;
    cornerPosition: "left" | "right";
    showCornerOnCover: boolean;
    cornerAnchor: "corner" | "margin";
    cornerPages: "all_except_cover" | "all" | "none";
    cornerHeightMm: number;
  };
}

/**
 * Theme sent as `theme_json` to /previews.
 * Returns undefined when the backend should derive everything itself
 * (logo upload → extract, otherwise neutral preset).
 */
export function resolvePreviewTheme(input: PreviewThemeInput): Theme | undefined {
  const base = input.studioTheme ?? input.storeTheme;
  const primary = input.brandPrimary.toUpperCase();
  const customised = primary !== DEFAULT_BRAND;

  if (!base && !customised) return undefined;

  let theme: Theme = base ?? {
    name: "Studio theme",
    palette: {
      primary,
      primary_dark: deriveBrandTint(primary).primaryDark,
      primary_tint: deriveBrandTint(primary).primaryTint,
      secondary: "#2C3A36",
      accent: "#C45C26",
      text: "#1A1714",
      muted: "#5C5348",
      surface: "#F6F2EA",
      info: "#175CD3",
      warning: "#B54708",
      success: "#067647",
      danger: "#B42318",
    },
    fonts: { heading: "Carlito", body: "Carlito", mono: "Liberation Mono" },
    border: { style: "single", width_pt: 1.5, color: primary, offset_pt: 24 },
    source: "manual",
  };

  if (base && base.palette.primary.toUpperCase() !== primary) {
    theme = applyBrandPrimary(base, primary);
  }

  const logos: LogoSet = {
    cover: input.hasCover ? (theme.logos?.cover ?? null) : null,
    corner: theme.logos?.corner ?? null,
    same_for_both: input.flags.sameForBoth,
    corner_position: input.flags.cornerPosition,
    corner_anchor: input.flags.cornerAnchor,
    corner_pages: input.flags.cornerPages,
    corner_height_mm: input.flags.cornerHeightMm,
    show_corner_on_cover: input.flags.showCornerOnCover,
    palette_source: theme.logos?.palette_source ?? "cover",
  };

  return {
    ...theme,
    logos,
    logo_path: input.hasCover ? theme.logo_path : null,
  };
}
