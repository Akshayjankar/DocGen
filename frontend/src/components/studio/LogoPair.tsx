"use client";

import { useCallback, useState } from "react";
import { toast } from "sonner";
import { CornerPlacementControl } from "@/components/studio/CornerPlacementControl";
import { LogoCard } from "@/components/studio/LogoCard";
import { extractTheme, uploadLogo } from "@/lib/api";
import { extractDominantColorFromFile } from "@/lib/color";
import { useStudioStore } from "@/lib/studio-store";
import { useThemeStore } from "@/lib/theme-store";
import { cn } from "@/lib/cn";
import type { Theme } from "@/types/api";

function themeFromPrimary(primary: string): Theme {
  return {
    name: "Logo theme",
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
    border: { style: "double", width_pt: 1.25, color: primary, offset_pt: 20 },
    source: "logo",
  };
}

function assetChip(id: string | undefined): string {
  if (!id) return "—";
  return `#${id.replace(/-/g, "").slice(0, 4)}`;
}

function Check({
  checked,
  onChange,
  disabled,
  children,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  disabled?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label
      className={cn(
        "inline-flex items-center gap-1.5",
        disabled ? "opacity-50" : "cursor-pointer",
      )}
    >
      <input
        type="checkbox"
        className="accent-[var(--brand)]"
        checked={checked}
        disabled={disabled}
        onChange={(e) => onChange(e.target.checked)}
      />
      {children}
    </label>
  );
}

export function LogoPair({ className }: { className?: string }) {
  const coverFile = useStudioStore((s) => s.coverFile);
  const cornerFile = useStudioStore((s) => s.cornerFile);
  const coverPreviewUrl = useStudioStore((s) => s.coverPreviewUrl);
  const cornerPreviewUrl = useStudioStore((s) => s.cornerPreviewUrl);
  const coverAsset = useStudioStore((s) => s.coverAsset);
  const cornerAsset = useStudioStore((s) => s.cornerAsset);
  const sameForBoth = useStudioStore((s) => s.sameForBoth);
  const cornerPosition = useStudioStore((s) => s.cornerPosition);
  const setCoverLogo = useStudioStore((s) => s.setCoverLogo);
  const setCornerLogo = useStudioStore((s) => s.setCornerLogo);
  const setLogoFlags = useStudioStore((s) => s.setLogoFlags);
  const setTheme = useStudioStore((s) => s.setTheme);
  const setThemeFromApi = useThemeStore((s) => s.setThemeFromApi);
  const setBrandPrimary = useThemeStore((s) => s.setBrandPrimary);
  const clearBrand = useThemeStore((s) => s.clearBrand);
  const [busy, setBusy] = useState<"cover" | "corner" | null>(null);

  const applyTheme = useCallback(
    (theme: Theme, url: string | null) => {
      setTheme(theme);
      setThemeFromApi(theme, url);
      setBrandPrimary(theme.palette.primary);
    },
    [setBrandPrimary, setTheme, setThemeFromApi],
  );

  const applyCover = useCallback(
    async (file: File) => {
      const url = URL.createObjectURL(file);
      setCoverLogo(file, url, null);
      setBusy("cover");
      try {
        const res = await uploadLogo(file, { role: "cover" });
        setCoverLogo(file, url, res.asset);
        if (res.palette_theme) {
          applyTheme(res.palette_theme, url);
          toast.success("Theme extracted from logo");
        } else {
          applyTheme(await extractTheme(file), url);
        }
      } catch {
        try {
          const primary = await extractDominantColorFromFile(file);
          applyTheme(themeFromPrimary(primary), url);
          toast.message("Brand color sampled from logo (logo service offline)");
        } catch {
          toast.error("Could not read logo colors");
        }
      } finally {
        setBusy(null);
      }
    },
    [applyTheme, setCoverLogo],
  );

  const applyCorner = useCallback(
    async (file: File) => {
      const url = URL.createObjectURL(file);
      setCornerLogo(file, url, null);
      setBusy("corner");
      try {
        const res = await uploadLogo(file, { role: "corner", extractPalette: false });
        setCornerLogo(file, url, res.asset);
      } catch {
        toast.message("Corner logo kept locally (logo service offline)");
      } finally {
        setBusy(null);
      }
    },
    [setCornerLogo],
  );

  const clearCover = () => {
    setCoverLogo(null, null, null);
    setTheme(null);
    clearBrand();
  };

  const hasCorner = sameForBoth ? !!coverFile : !!cornerFile;
  const showDevChips = process.env.NODE_ENV === "development";

  return (
    <div className={cn("flex flex-col gap-3", className)}>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <LogoCard
          role="cover"
          label="Cover logo"
          hint="Centered on cover"
          previewUrl={coverPreviewUrl}
          asset={coverAsset}
          busy={busy === "cover"}
          onFile={(f) => void applyCover(f)}
          onClear={clearCover}
          onInvalid={(m) => toast.error(m)}
        />
        <LogoCard
          role="corner"
          label="Corner logo"
          hint={`Header · ${cornerPosition}`}
          previewUrl={sameForBoth ? coverPreviewUrl : cornerPreviewUrl}
          asset={sameForBoth ? coverAsset : cornerAsset}
          busy={busy === "corner"}
          mirrored={sameForBoth}
          disabled={sameForBoth}
          onFile={(f) => void applyCorner(f)}
          onClear={() => setCornerLogo(null, null, null)}
          onInvalid={(m) => toast.error(m)}
        />
      </div>

      {showDevChips ? (
        <p className="font-mono text-[10px] text-fg-muted">
          cover {assetChip(coverAsset?.id)} · corner{" "}
          {assetChip(sameForBoth ? coverAsset?.id : cornerAsset?.id)}
        </p>
      ) : null}

      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-fg-muted">
        <Check
          checked={sameForBoth}
          disabled={!coverFile && !sameForBoth}
          onChange={(v) => setLogoFlags({ sameForBoth: v })}
        >
          Use cover for both
        </Check>
      </div>

      <CornerPlacementControl disabled={!hasCorner} />
    </div>
  );
}
