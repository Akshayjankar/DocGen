import { describe, expect, it } from "vitest";
import {
  ambientFromPalette,
  clampAmbientOklch,
  hexToOklch,
} from "@/lib/color";

describe("ambient OKLCH", () => {
  it("clamps lightness and chroma for dark glow", () => {
    const hot = clampAmbientOklch({ l: 0.9, c: 0.3, h: 30 });
    expect(hot.l).toBeGreaterThanOrEqual(0.5);
    expect(hot.l).toBeLessThanOrEqual(0.68);
    expect(hot.c).toBeGreaterThanOrEqual(0.06);
    expect(hot.c).toBeLessThanOrEqual(0.17);
  });

  it("falls back for near-gray logos", () => {
    const gray = clampAmbientOklch(hexToOklch("#888888"));
    expect(gray.c).toBeLessThanOrEqual(0.06);
    expect(gray.h).toBeCloseTo(250, 0);
  });

  it("builds three ambient CSS colors from a blue primary", () => {
    const amb = ambientFromPalette("#1E64C8", "#4A5568", "#2B6CB0");
    expect(amb.amb1).toMatch(/^oklch\(/);
    expect(amb.amb2).toMatch(/^oklch\(/);
    expect(amb.amb3).toMatch(/^oklch\(/);
  });
});
