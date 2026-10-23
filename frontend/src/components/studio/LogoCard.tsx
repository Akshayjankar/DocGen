"use client";

import { Image as ImageIcon, SpinnerGap, Warning, X } from "@phosphor-icons/react";
import { useRef, useState } from "react";
import { cn } from "@/lib/cn";
import type { LogoAsset, LogoRole } from "@/types/api";

const ACCEPT =
  "image/png,image/jpeg,image/svg+xml,image/webp,.png,.jpg,.jpeg,.svg,.webp";
const IMAGE_RE = /\.(png|jpe?g|svg|webp)$/i;

const BG_LABEL: Partial<Record<LogoAsset["background"], string>> = {
  removed: "Background removed",
  was_transparent: "Transparent",
};

function humanize(code: string) {
  const s = code.replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export interface LogoCardProps {
  role: LogoRole;
  label: string;
  hint: string;
  previewUrl: string | null;
  asset: LogoAsset | null;
  busy?: boolean;
  /** Card shows the cover logo read-only (Use cover for both). */
  mirrored?: boolean;
  disabled?: boolean;
  onFile: (file: File) => void;
  onClear: () => void;
  onInvalid?: (message: string) => void;
}

export function LogoCard({
  role,
  label,
  hint,
  previewUrl,
  asset,
  busy,
  mirrored,
  disabled,
  onFile,
  onClear,
  onInvalid,
}: LogoCardProps) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const accept = (f: File | undefined) => {
    if (!f || disabled) return;
    if (!f.type.startsWith("image/") && !IMAGE_RE.test(f.name)) {
      onInvalid?.("Use a logo image (PNG, JPG, SVG, WebP).");
      return;
    }
    onFile(f);
  };

  const chips: { text: string; warn: boolean }[] = [];
  const bg = asset ? BG_LABEL[asset.background] : undefined;
  if (bg) chips.push({ text: bg, warn: false });
  for (const w of asset?.warnings ?? []) chips.push({ text: humanize(w), warn: true });

  return (
    <div
      className={cn(
        "flex min-w-0 flex-col gap-2 rounded-[var(--radius-md)] border border-border bg-surface p-3",
        disabled && "opacity-60",
      )}
    >
      <div className="flex items-baseline justify-between gap-2">
        <p className="text-sm font-medium text-fg">{label}</p>
        <span className="text-[11px] text-fg-muted">{hint}</span>
      </div>

      <div
        className={cn(
          "relative flex aspect-[16/9] w-full items-center justify-center overflow-hidden rounded-[var(--radius-sm)] border border-dashed transition-colors",
          dragging ? "border-brand bg-brand-tint/40" : "border-border bg-surface-2/40",
          !disabled && "hover:border-brand/50",
        )}
        onDragEnter={(e) => {
          e.preventDefault();
          if (!disabled) setDragging(true);
        }}
        onDragLeave={(e) => {
          if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setDragging(false);
        }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          accept(e.dataTransfer.files?.[0]);
        }}
      >
        <button
          type="button"
          disabled={disabled}
          onClick={() => inputRef.current?.click()}
          aria-label={
            previewUrl ? `Replace ${label.toLowerCase()}` : `Upload ${label.toLowerCase()}`
          }
          className="absolute inset-0 flex items-center justify-center focus-visible:outline-2 focus-visible:outline-brand"
        >
          {previewUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={previewUrl}
              alt={asset?.alt_text || `${label} preview`}
              className="max-h-full max-w-full object-contain p-2"
            />
          ) : (
            <span className="flex flex-col items-center gap-1 text-fg-muted">
              {busy ? (
                <SpinnerGap className="animate-spin text-brand" size={22} />
              ) : (
                <ImageIcon className="text-brand" size={22} weight="duotone" />
              )}
              <span className="text-xs">{dragging ? "Release to upload" : "Drop or click"}</span>
            </span>
          )}
        </button>
        {previewUrl && busy ? (
          <SpinnerGap
            className="absolute bottom-1.5 left-1.5 animate-spin text-brand"
            size={14}
          />
        ) : null}
        {previewUrl && !mirrored ? (
          <button
            type="button"
            className="absolute right-1.5 top-1.5 rounded-full bg-surface/90 p-1 text-fg-muted shadow-sm hover:text-fg"
            aria-label={`Remove ${label.toLowerCase()}`}
            onClick={onClear}
          >
            <X size={14} />
          </button>
        ) : null}
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          className="sr-only"
          tabIndex={-1}
          onChange={(e) => {
            accept(e.target.files?.[0]);
            e.target.value = "";
          }}
        />
      </div>

      {chips.length ? (
        <ul className="flex flex-wrap gap-1.5" aria-label={`${label} notes`}>
          {chips.map((c) => (
            <li
              key={c.text}
              className={cn(
                "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px]",
                c.warn
                  ? "border-warning/40 bg-warning/10 text-warning"
                  : "border-border bg-surface-2 text-fg-muted",
              )}
            >
              {c.warn ? <Warning size={11} weight="fill" /> : null}
              {c.text}
            </li>
          ))}
        </ul>
      ) : null}
      <span className="sr-only">{role} logo</span>
    </div>
  );
}
