"use client";

import { Drop, SpinnerGap } from "@phosphor-icons/react";
import { motion } from "motion/react";
import { useCallback, useRef, useState } from "react";
import { toast } from "sonner";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { extractTheme } from "@/lib/api";
import { extractDominantColorFromFile } from "@/lib/color";
import { announce } from "@/lib/a11y";
import { fadeUp, springSoft } from "@/lib/motion";
import { useThemeStore } from "@/lib/theme-store";
import { cn } from "@/lib/cn";
import type { Theme } from "@/types/api";

function localTheme(primary: string, name: string): Theme {
  return {
    name,
    palette: {
      primary,
      primary_dark: primary,
      primary_tint: "#E8EEF5",
      secondary: "#4A5568",
      accent: primary,
      text: "#1A1A1A",
      muted: "#5C5C5C",
      surface: "#FFFFFF",
      info: "#2B6CB0",
      warning: "#B7791F",
      success: "#276749",
      danger: "#C53030",
    },
    fonts: { heading: "Carlito", body: "Carlito", mono: "Liberation Mono" },
    border: { style: "single", width_pt: 1.5, color: primary, offset_pt: 24 },
    source: "logo",
  };
}

interface ChromaDropProps {
  onReady?: () => void;
  className?: string;
}

export function ChromaDrop({ onReady, className }: ChromaDropProps) {
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const dragDepth = useRef(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const reduced = useReducedMotion();
  const setThemeFromApi = useThemeStore((s) => s.setThemeFromApi);
  const setBrandPrimary = useThemeStore((s) => s.setBrandPrimary);
  const logoPreviewUrl = useThemeStore((s) => s.logoPreviewUrl);
  const brandPrimary = useThemeStore((s) => s.brandPrimary);

  const openPicker = useCallback(() => {
    if (!busy) inputRef.current?.click();
  }, [busy]);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.type.startsWith("image/") && !file.name.match(/\.(png|jpe?g|svg|webp)$/i)) {
        toast.error("Drop a logo image (PNG, JPG, SVG, WebP).");
        return;
      }
      setBusy(true);
      const localUrl = URL.createObjectURL(file);
      try {
        const theme = await extractTheme(file);
        setThemeFromApi(theme, localUrl);
        announce(`Brand extracted: ${theme.name}. Interface re-tinted.`);
        toast.success("Chroma locked — UI re-tinted to your brand.");
        onReady?.();
      } catch {
        try {
          const primary = await extractDominantColorFromFile(file);
          const theme = localTheme(primary, file.name || "Logo");
          setThemeFromApi(theme, localUrl);
          setBrandPrimary(primary);
          announce("Logo received. Brand color sampled locally.");
          toast.message("Logo dropped — brand color sampled from image.");
        } catch {
          useThemeStore.setState({ logoPreviewUrl: localUrl, logoFileName: file.name });
          setBrandPrimary(brandPrimary);
          toast.error("Could not sample logo colors");
        }
        onReady?.();
      } finally {
        setBusy(false);
      }
    },
    [brandPrimary, onReady, setBrandPrimary, setThemeFromApi],
  );

  return (
    <motion.div
      variants={reduced ? undefined : fadeUp}
      initial={reduced ? false : "hidden"}
      animate="show"
      className={cn("relative w-full", className)}
    >
      <div
        role="button"
        tabIndex={0}
        aria-label="Drop your company logo or click to browse"
        onClick={openPicker}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            openPicker();
          }
        }}
        onDragEnter={(e) => {
          e.preventDefault();
          e.stopPropagation();
          dragDepth.current += 1;
          setDragging(true);
        }}
        onDragOver={(e) => {
          e.preventDefault();
          e.stopPropagation();
          e.dataTransfer.dropEffect = "copy";
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          e.stopPropagation();
          dragDepth.current = Math.max(0, dragDepth.current - 1);
          if (dragDepth.current === 0) setDragging(false);
        }}
        onDrop={(e) => {
          e.preventDefault();
          e.stopPropagation();
          dragDepth.current = 0;
          setDragging(false);
          const file = e.dataTransfer.files?.[0];
          if (file) void handleFile(file);
        }}
        className={cn(
          "group relative flex min-h-[min(70vh,28rem)] w-full cursor-pointer flex-col items-center justify-center overflow-hidden rounded-[var(--radius-lg)] border-[3px] border-dashed px-8 py-16 text-center transition-all sm:min-h-[32rem] sm:px-16 sm:py-20",
          dragging
            ? "border-brand bg-brand-tint scale-[1.01]"
            : "border-border bg-surface/80 hover:border-brand/60",
        )}
        style={{
          boxShadow: dragging
            ? `0 0 0 6px color-mix(in srgb, ${brandPrimary} 25%, transparent)`
            : undefined,
        }}
      >
        <input
          ref={inputRef}
          id="chroma-file"
          type="file"
          accept="image/png,image/jpeg,image/svg+xml,image/webp,.png,.jpg,.jpeg,.svg,.webp"
          className="sr-only"
          onClick={(e) => e.stopPropagation()}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleFile(file);
            e.target.value = "";
          }}
        />

        <motion.div
          animate={
            reduced
              ? undefined
              : dragging
                ? { y: 4, scale: 1.06 }
                : { y: [0, -8, 0], scale: 1 }
          }
          transition={
            dragging
              ? springSoft
              : { duration: 3.2, repeat: Infinity, ease: "easeInOut" }
          }
          className="mb-8 flex size-28 items-center justify-center rounded-full bg-brand-tint text-brand sm:size-36"
        >
          {busy ? (
            <SpinnerGap size={48} className="animate-spin" />
          ) : logoPreviewUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={logoPreviewUrl}
              alt="Uploaded logo"
              className="size-20 object-contain sm:size-28"
            />
          ) : (
            <Drop size={64} weight="duotone" />
          )}
        </motion.div>

        <p className="font-display text-3xl font-semibold tracking-tight sm:text-5xl">
          {dragging ? "Release to load" : "Drop your logo"}
        </p>
        <p className="mx-auto mt-4 max-w-lg text-base text-fg-muted sm:text-lg">
          Click anywhere in this zone or drag an image — the Chroma Press re-tints
          live from your brand. Layout stays deterministic.
        </p>
        <p className="mt-8 font-mono text-xs uppercase tracking-[0.2em] text-fg-muted sm:text-sm">
          PNG · JPG · SVG · WebP · large drop target
        </p>
      </div>
    </motion.div>
  );
}
