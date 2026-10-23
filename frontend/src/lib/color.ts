/** Hex color helpers for brand tinting and contrast (WCAG AA). */

export type Hex = `#${string}`;

const HEX_RE = /^#([0-9A-Fa-f]{6})$/;

export function normalizeHex(input: string): Hex {
  let v = input.trim();
  if (!v.startsWith("#")) v = `#${v}`;
  if (v.length === 4) {
    v = `#${v[1]}${v[1]}${v[2]}${v[2]}${v[3]}${v[3]}`;
  }
  if (!HEX_RE.test(v)) {
    throw new Error(`Invalid hex color: ${input}`);
  }
  return v.toUpperCase() as Hex;
}

export function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const h = normalizeHex(hex).slice(1);
  return {
    r: parseInt(h.slice(0, 2), 16),
    g: parseInt(h.slice(2, 4), 16),
    b: parseInt(h.slice(4, 6), 16),
  };
}

export function rgbToHex(r: number, g: number, b: number): Hex {
  const clamp = (n: number) => Math.max(0, Math.min(255, Math.round(n)));
  return `#${[clamp(r), clamp(g), clamp(b)]
    .map((n) => n.toString(16).padStart(2, "0"))
    .join("")
    .toUpperCase()}` as Hex;
}

function srgbChannel(c: number): number {
  const s = c / 255;
  return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
}

/** Relative luminance (WCAG). */
export function relativeLuminance(hex: string): number {
  const { r, g, b } = hexToRgb(hex);
  return 0.2126 * srgbChannel(r) + 0.7152 * srgbChannel(g) + 0.0722 * srgbChannel(b);
}

/** Contrast ratio between two hex colors. */
export function contrastRatio(fg: string, bg: string): number {
  const l1 = relativeLuminance(fg);
  const l2 = relativeLuminance(bg);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

export function meetsAa(fg: string, bg: string, large = false): boolean {
  return contrastRatio(fg, bg) >= (large ? 3 : 4.5);
}

/** Mix two hex colors (t in 0..1 toward `b`). */
export function mix(a: string, b: string, t: number): Hex {
  const A = hexToRgb(a);
  const B = hexToRgb(b);
  return rgbToHex(
    A.r + (B.r - A.r) * t,
    A.g + (B.g - A.g) * t,
    A.b + (B.b - A.b) * t,
  );
}

export function lighten(hex: string, amount = 0.2): Hex {
  return mix(hex, "#FFFFFF", amount);
}

export function darken(hex: string, amount = 0.2): Hex {
  return mix(hex, "#000000", amount);
}

/** Derive a soft UI tint palette from a primary brand color. */
export function deriveBrandTint(primary: string) {
  const p = normalizeHex(primary);
  return {
    primary: p,
    primaryDark: darken(p, 0.28),
    primaryTint: lighten(p, 0.82),
    secondary: darken(mix(p, "#2A2A2A", 0.35), 0.1),
    accent: mix(p, "#C45C26", 0.35),
    ink: "#1A1714",
    paper: "#F6F2EA",
  };
}

/** CSS custom property map for live brand re-tint. */
export function brandToCssVars(primary: string): Record<string, string> {
  const t = deriveBrandTint(primary);
  return {
    "--brand": t.primary,
    "--brand-dark": t.primaryDark,
    "--brand-tint": t.primaryTint,
    "--brand-secondary": t.secondary,
    "--brand-accent": t.accent,
  };
}

/**
 * Sample a logo image in the browser and return the most saturated
 * non-near-white / non-near-black color (fallback when theme API is offline).
 */
export async function extractDominantColorFromFile(file: File): Promise<Hex> {
  const bitmap = await createImageBitmap(file);
  const size = 64;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  if (!ctx) {
    bitmap.close();
    return "#1F6F5B";
  }
  ctx.drawImage(bitmap, 0, 0, size, size);
  bitmap.close();
  const { data } = ctx.getImageData(0, 0, size, size);

  type Bucket = { r: number; g: number; b: number; w: number };
  const buckets = new Map<string, Bucket>();

  for (let i = 0; i < data.length; i += 4) {
    const a = data[i + 3] ?? 0;
    if (a < 40) continue;
    const r = data[i] ?? 0;
    const g = data[i + 1] ?? 0;
    const b = data[i + 2] ?? 0;
    // Skip near-white / near-black backgrounds
    if (r > 245 && g > 245 && b > 245) continue;
    if (r < 18 && g < 18 && b < 18) continue;
    const qr = r >> 4;
    const qg = g >> 4;
    const qb = b >> 4;
    const key = `${qr},${qg},${qb}`;
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    const sat = max === 0 ? 0 : (max - min) / max;
    const weight = 1 + sat * 4;
    const prev = buckets.get(key);
    if (prev) {
      prev.r += r * weight;
      prev.g += g * weight;
      prev.b += b * weight;
      prev.w += weight;
    } else {
      buckets.set(key, { r: r * weight, g: g * weight, b: b * weight, w: weight });
    }
  }

  if (buckets.size === 0) return "#1F6F5B";

  let best: Bucket | null = null;
  let bestScore = -1;
  for (const bucket of buckets.values()) {
    const r = bucket.r / bucket.w;
    const g = bucket.g / bucket.w;
    const b = bucket.b / bucket.w;
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    const sat = max === 0 ? 0 : (max - min) / max;
    const score = bucket.w * (0.35 + sat);
    if (score > bestScore) {
      bestScore = score;
      best = bucket;
    }
  }
  if (!best) return "#1F6F5B";
  return rgbToHex(best.r / best.w, best.g / best.w, best.b / best.w);
}

/* ── OKLCH ambient helpers (Revision 3) ─────────────────────────────── */

export type Oklch = { l: number; c: number; h: number };

function linearSrgbChannel(c: number): number {
  const s = c / 255;
  return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
}

/** sRGB hex → OKLCH (L, C, H in CSS oklch units). */
export function hexToOklch(hex: string): Oklch {
  const { r, g, b } = hexToRgb(hex);
  const lr = linearSrgbChannel(r);
  const lg = linearSrgbChannel(g);
  const lb = linearSrgbChannel(b);

  const l = 0.4122214708 * lr + 0.5363325363 * lg + 0.0514459929 * lb;
  const m = 0.2119034982 * lr + 0.6806995451 * lg + 0.1073969566 * lb;
  const s = 0.0883024619 * lr + 0.2817188376 * lg + 0.6299787005 * lb;

  const l_ = Math.cbrt(l);
  const m_ = Math.cbrt(m);
  const s_ = Math.cbrt(s);

  const L = 0.2104542553 * l_ + 0.793617785 * m_ - 0.0040720468 * s_;
  const a = 1.9779984951 * l_ - 2.428592205 * m_ + 0.4505937099 * s_;
  const bLab = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.808675766 * s_;

  const c = Math.sqrt(a * a + bLab * bLab);
  let h = (Math.atan2(bLab, a) * 180) / Math.PI;
  if (h < 0) h += 360;

  return { l: L, c, h };
}

/** Clamp ambient OKLCH for soft Studio glows; desaturated → cool neutral. */
export function clampAmbientOklch({ l, c, h }: Oklch): Oklch {
  if (c < 0.03) {
    return { l: 0.58, c: 0.04, h: 250 };
  }
  return {
    l: Math.max(0.5, Math.min(0.68, l)),
    c: Math.max(0.06, Math.min(0.17, c)),
    h,
  };
}

function oklchCss(o: Oklch): string {
  return `oklch(${o.l.toFixed(3)} ${o.c.toFixed(3)} ${o.h.toFixed(1)})`;
}

/** Three ambient CSS colors from brand palette (primary / secondary / tint). */
export function ambientFromPalette(
  primary: string,
  secondary?: string,
  accent?: string,
): { amb1: string; amb2: string; amb3: string } {
  const tint = deriveBrandTint(primary).primaryTint;
  const amb1 = clampAmbientOklch(hexToOklch(primary));
  const amb2 = clampAmbientOklch(hexToOklch(secondary ?? accent ?? primary));
  const amb3 = clampAmbientOklch(hexToOklch(accent ?? tint));
  return {
    amb1: oklchCss(amb1),
    amb2: oklchCss(amb2),
    amb3: oklchCss(amb3),
  };
}

/** CSS custom properties for ambient glow layers. */
export function ambientToCssVars(
  primary: string,
  secondary?: string,
  accent?: string,
): Record<string, string> {
  const { amb1, amb2, amb3 } = ambientFromPalette(primary, secondary, accent);
  return {
    "--amb-1": amb1,
    "--amb-2": amb2,
    "--amb-3": amb3,
  };
}
