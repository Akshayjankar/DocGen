"use client";

import { useTheme } from "next-themes";
import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { ambientFromPalette } from "@/lib/color";
import { useStudioStore } from "@/lib/studio-store";
import { useThemeStore } from "@/lib/theme-store";
import { cn } from "@/lib/cn";

const DARKROOM = "#0B0B12";

function layerStyle(
  amb: { amb1: string; amb2: string; amb3: string },
  light: boolean,
): CSSProperties {
  const a1 = light ? 0.05 : 0.16;
  const a2 = light ? 0.04 : 0.12;
  const a3 = light ? 0.03 : 0.08;
  return {
    backgroundColor: light ? "transparent" : DARKROOM,
    backgroundImage: `
      radial-gradient(
        ellipse 85% 65% at 12% 8%,
        color-mix(in oklch, ${amb.amb1} ${Math.round(a1 * 100)}%, transparent),
        transparent 58%
      ),
      radial-gradient(
        ellipse 70% 55% at 88% 18%,
        color-mix(in oklch, ${amb.amb2} ${Math.round(a2 * 100)}%, transparent),
        transparent 52%
      ),
      radial-gradient(
        ellipse 60% 45% at 50% 95%,
        color-mix(in oklch, ${amb.amb3} ${Math.round(a3 * 100)}%, transparent),
        transparent 48%
      )
    `,
  };
}

export function AmbientGlow({
  enabled = true,
  className,
}: {
  enabled?: boolean;
  className?: string;
}) {
  const { resolvedTheme } = useTheme();
  const brandPrimary = useThemeStore((s) => s.brandPrimary);
  const storeTheme = useThemeStore((s) => s.theme);
  const studioTheme = useStudioStore((s) => s.theme);

  const palette = studioTheme?.palette ?? storeTheme?.palette;
  const primary = palette?.primary ?? brandPrimary;

  const amb = useMemo(
    () =>
      ambientFromPalette(
        primary,
        palette?.secondary,
        palette?.accent ?? palette?.primary_tint,
      ),
    [primary, palette?.secondary, palette?.accent, palette?.primary_tint],
  );

  const ambKey = `${amb.amb1}|${amb.amb2}|${amb.amb3}`;
  const [front, setFront] = useState(0);
  const [layers, setLayers] = useState<[typeof amb, typeof amb]>([amb, amb]);
  const prevKey = useRef(ambKey);

  useEffect(() => {
    if (prevKey.current === ambKey) return;
    prevKey.current = ambKey;
    setFront((f) => {
      const nextFront = f === 0 ? 1 : 0;
      setLayers((prev) => {
        const next: [typeof amb, typeof amb] = [...prev];
        next[nextFront] = amb;
        return next;
      });
      return nextFront;
    });
  }, [ambKey, amb]);

  const [paused, setPaused] = useState(false);

  useEffect(() => {
    const onVis = () => setPaused(document.hidden);
    document.addEventListener("visibilitychange", onVis);
    const conn = (
      navigator as Navigator & { connection?: { saveData?: boolean } }
    ).connection;
    if (conn?.saveData) setPaused(true);
    return () => document.removeEventListener("visibilitychange", onVis);
  }, []);

  const light = resolvedTheme === "light";
  const reduced =
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (!enabled) return null;

  return (
    <div
      aria-hidden
      className={cn(
        "pointer-events-none fixed inset-0 z-0 overflow-hidden",
        className,
      )}
    >
      {[0, 1].map((i) => (
        <div
          key={i}
          className={cn(
            "absolute inset-0 transition-opacity duration-[900ms] ease-out",
            i === front ? "opacity-100" : "opacity-0",
            !reduced && !paused && "animate-ambient-glow-drift",
          )}
          style={{
            ...layerStyle(layers[i] ?? amb, light),
            animationPlayState: paused ? "paused" : "running",
          }}
        />
      ))}
    </div>
  );
}
