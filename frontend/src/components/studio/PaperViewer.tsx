"use client";

import { ArrowClockwise, SpinnerGap } from "@phosphor-icons/react";
import { useEffect, useRef, useState } from "react";
import { createPreview, previewPageUrl } from "@/lib/api";
import { resolvePreviewTheme } from "@/lib/preview-theme";
import { useStudioStore } from "@/lib/studio-store";
import { useThemeStore } from "@/lib/theme-store";
import { cn } from "@/lib/cn";
import type { PreviewPage } from "@/types/api";

const DEBOUNCE_MS = 900;

/**
 * Paper from a backend PreviewSession (PNG pages of the real PDF).
 * Export reuses the same session, so what you see is what you download.
 */
export function PaperViewer({ className }: { className?: string }) {
  const text = useStudioStore((s) => s.text);
  const meta = useStudioStore((s) => s.meta);
  const studioTheme = useStudioStore((s) => s.theme);
  const coverFile = useStudioStore((s) => s.coverFile);
  const cornerFile = useStudioStore((s) => s.cornerFile);
  const formatId = useStudioStore((s) => s.formatId);
  const sameForBoth = useStudioStore((s) => s.sameForBoth);
  const cornerPosition = useStudioStore((s) => s.cornerPosition);
  const showCornerOnCover = useStudioStore((s) => s.showCornerOnCover);
  const cornerAnchor = useStudioStore((s) => s.cornerAnchor);
  const cornerPages = useStudioStore((s) => s.cornerPages);
  const cornerHeightMm = useStudioStore((s) => s.cornerHeightMm);
  const setPreview = useStudioStore((s) => s.setPreview);
  const setPreviewState = useStudioStore((s) => s.setPreviewState);
  const storeTheme = useThemeStore((s) => s.theme);
  const brandPrimary = useThemeStore((s) => s.brandPrimary);

  const [pages, setPages] = useState<PreviewPage[]>([]);
  const [previewId, setPreviewId] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "draft" | "building" | "exact" | "error">(
    "idle",
  );
  const [ms, setMs] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const [active, setActive] = useState(1);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ac = new AbortController();
    setStatus("draft");
    setPreviewState("draft");

    const timer = setTimeout(async () => {
      setStatus("building");
      try {
        const theme = resolvePreviewTheme({
          studioTheme,
          storeTheme,
          brandPrimary,
          hasCover: !!coverFile,
          flags: {
            sameForBoth,
            cornerPosition,
            showCornerOnCover,
            cornerAnchor,
            cornerPages,
            cornerHeightMm,
          },
        });
        const res = await createPreview({
          text: text || " ",
          meta,
          formatId,
          logoCover: coverFile,
          logoCorner: sameForBoth ? coverFile : cornerFile,
          theme,
          signal: ac.signal,
        });
        if (ac.signal.aborted) return;
        setPages(res.pages);
        setPreviewId(res.preview_id);
        setPreview(res.preview_id, res.page_count);
        setMs(res.duration_ms);
        setError(null);
        setStatus("exact");
        setPreviewState("exact");
      } catch (e) {
        if (ac.signal.aborted || (e as Error).name === "AbortError") return;
        setError(e instanceof Error ? e.message : "Preview failed");
        setStatus("error");
        setPreviewState("error");
      }
    }, DEBOUNCE_MS);

    return () => {
      clearTimeout(timer);
      ac.abort();
    };
  }, [
    text,
    meta,
    studioTheme,
    storeTheme,
    brandPrimary,
    formatId,
    coverFile,
    cornerFile,
    sameForBoth,
    cornerPosition,
    showCornerOnCover,
    cornerAnchor,
    cornerPages,
    cornerHeightMm,
    retry,
    setPreview,
    setPreviewState,
  ]);

  const goTo = (n: number) => {
    setActive(n);
    scrollRef.current
      ?.querySelector<HTMLElement>(`[data-page="${n}"]`)
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const label =
    status === "exact"
      ? "Exact"
      : status === "building"
        ? "Draft · rendering"
        : status === "draft"
          ? "Draft"
          : status === "error"
            ? "Offline"
            : "Paper";

  return (
    <div className={cn("flex h-full min-h-0 flex-col", className)}>
      <div className="flex items-center justify-between gap-3 border-b border-border px-1 pb-2 text-[11px] text-fg-muted">
        <span className="inline-flex items-center gap-2">
          <span
            aria-hidden
            className={cn(
              "size-2 rounded-full",
              status === "exact" && "bg-success",
              (status === "draft" || status === "building") && "bg-warning",
              status === "error" && "bg-danger",
              status === "idle" && "bg-border",
            )}
          />
          <span role="status" className="font-medium text-fg">
            {label}
          </span>
          {pages.length ? (
            <span>
              · {pages.length} page{pages.length === 1 ? "" : "s"}
            </span>
          ) : null}
        </span>
        <span className="inline-flex items-center gap-2 font-mono">
          {status === "building" ? (
            <SpinnerGap className="animate-spin" size={12} />
          ) : ms && status === "exact" ? (
            `${Math.round(ms)} ms`
          ) : null}
          {pages.length > 1 ? (
            <span className="inline-flex items-center gap-1" aria-label="Page navigation">
              {pages.map((p) => (
                <button
                  key={p.n}
                  type="button"
                  onClick={() => goTo(p.n)}
                  aria-label={`Go to page ${p.n}`}
                  aria-current={active === p.n}
                  className={cn(
                    "size-5 rounded text-[10px] transition-colors",
                    active === p.n
                      ? "bg-brand-tint text-brand"
                      : "hover:bg-surface-2 hover:text-fg",
                  )}
                >
                  {p.n}
                </button>
              ))}
            </span>
          ) : null}
        </span>
      </div>

      <div
        ref={scrollRef}
        className={cn(
          "mt-3 min-h-0 flex-1 overflow-auto rounded-[var(--radius-md)] bg-[color-mix(in_srgb,var(--fg)_6%,transparent)] p-4 transition-opacity",
          (status === "draft" || status === "building") && pages.length > 0 && "opacity-80",
        )}
      >
        {status === "error" && pages.length === 0 ? (
          <div className="mx-auto flex max-w-sm flex-col items-center gap-3 py-12 text-center">
            <p className="text-sm text-fg-muted">
              Can&apos;t reach the preview service. {error}
            </p>
            <button
              type="button"
              onClick={() => setRetry((n) => n + 1)}
              className="inline-flex items-center gap-1.5 text-sm font-medium text-brand hover:underline"
            >
              <ArrowClockwise size={14} /> Retry
            </button>
          </div>
        ) : pages.length === 0 ? (
          <div className="mx-auto flex h-[min(420px,55vh)] w-full max-w-[420px] flex-col justify-between rounded-sm border border-border/80 bg-[#fffdf8] p-8 shadow-[0_18px_50px_-28px_rgba(26,23,20,0.45)] dark:bg-surface">
            <div>
              <div className="h-2 w-16 rounded-full bg-brand/70" />
              <div className="mt-8 space-y-2.5">
                <div className="h-3 animate-pulse rounded bg-surface-2" />
                <div className="h-3 w-[88%] animate-pulse rounded bg-surface-2" />
                <div className="h-3 w-[72%] animate-pulse rounded bg-surface-2" />
                <div className="mt-4 h-3 w-[92%] animate-pulse rounded bg-surface-2" />
                <div className="h-3 w-[64%] animate-pulse rounded bg-surface-2" />
              </div>
            </div>
            <p className="text-center font-serif text-sm italic text-fg-muted">
              {text.trim() ? "Rendering paper…" : "Start typing — paper appears here"}
            </p>
          </div>
        ) : (
          <div className="mx-auto flex max-w-[560px] flex-col gap-6">
            {error ? (
              <p className="text-xs text-danger" role="alert">
                {error} — showing last good render.
              </p>
            ) : null}
            {pages.map((p) => (
              <figure key={p.n} data-page={p.n} className="m-0">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={previewId ? previewPageUrl(previewId, p.n) : p.png_url}
                  alt={`Page ${p.n} of ${pages.length}`}
                  width={p.w}
                  height={p.h}
                  className="h-auto w-full rounded-sm bg-white shadow-md"
                />
              </figure>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
