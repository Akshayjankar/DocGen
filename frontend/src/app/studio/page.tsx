"use client";

import { Palette, Printer, X } from "@phosphor-icons/react";
import { useCallback, useEffect, useState } from "react";
import { getDoc } from "@/lib/library-db";
import { getTemplate } from "@/lib/templates";
import { toast } from "sonner";
import { Button } from "@/components/ui/Button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/Tabs";
import { ContentSeal } from "@/components/studio/ContentSeal";
import { ContrastRing } from "@/components/studio/ContrastRing";
import { DiffReview } from "@/components/studio/DiffReview";
import { AmbientGlow } from "@/components/studio/AmbientGlow";
import { FormatPicker } from "@/components/studio/FormatPicker";
import { ExportBar } from "@/components/studio/ExportBar";
import { LintPanel } from "@/components/studio/LintPanel";
import { LogoPair } from "@/components/studio/LogoPair";
import { PaperViewer } from "@/components/studio/PaperViewer";
import { ModeSwitch } from "@/components/studio/ModeSwitch";
import { PressProgress } from "@/components/studio/PressProgress";
import { TextInput } from "@/components/studio/TextInput";
import { ThemeEditor } from "@/components/studio/ThemeEditor";
import { useJobStream } from "@/hooks/useJobStream";
import { createDocument, getJob } from "@/lib/api";
import { announce } from "@/lib/a11y";
import { useStudioStore } from "@/lib/studio-store";
import { useThemeStore } from "@/lib/theme-store";
import { cn } from "@/lib/cn";
import type { LintItem, Mode, Theme } from "@/types/api";

function buildFallbackTheme(primary: string): Theme {
  return {
    name: "Studio theme",
    palette: {
      primary,
      primary_dark: primary,
      primary_tint: "#E4F2ED",
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
    fonts: {
      heading: "Calibri",
      body: "Calibri",
      mono: "Consolas",
    },
    border: {
      style: "single",
      width_pt: 1.5,
      color: primary,
      offset_pt: 24,
    },
    source: "manual",
  };
}

function BrandPanel({
  preservedPct,
  mode,
  documentId,
  status,
  lint,
  onClose,
}: {
  preservedPct: number | null;
  mode: Mode;
  documentId: string | null;
  status: string | null;
  lint: LintItem[];
  onClose?: () => void;
}) {
  const brandGlow = useStudioStore((s) => s.brandGlow);
  const setBrandGlow = useStudioStore((s) => s.setBrandGlow);

  return (
    <div className="flex h-full min-h-0 flex-col gap-3 overflow-auto p-3">
      <div className="flex items-center justify-between gap-2">
        <p className="font-display text-sm font-semibold">Brand & checks</p>
        {onClose ? (
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-1.5 text-fg-muted hover:bg-surface-2 hover:text-fg lg:hidden"
            aria-label="Close brand panel"
          >
            <X size={16} />
          </button>
        ) : null}
      </div>

      {/* Downloads first — always visible when panel opens after press */}
      <div className="rounded-[var(--radius-md)] border-2 border-brand/40 bg-brand-tint/40 p-1">
        <p className="px-2 pt-2 text-[11px] font-medium uppercase tracking-wider text-brand">
          Your files
        </p>
        <ExportBar documentId={documentId} />
      </div>

      <ContentSeal preservedPct={preservedPct} mode={mode} />
      <label className="flex cursor-pointer items-center gap-2 text-xs text-fg-muted">
        <input
          type="checkbox"
          className="accent-[var(--brand)]"
          checked={brandGlow}
          onChange={(e) => setBrandGlow(e.target.checked)}
        />
        Ambient brand glow (Studio backdrop)
      </label>
      <ThemeEditor />
      <ContrastRing />
      <Tabs defaultValue="lint">
        <TabsList>
          <TabsTrigger value="lint">Lint</TabsTrigger>
          <TabsTrigger value="diffs">Diffs</TabsTrigger>
        </TabsList>
        <TabsContent value="lint">
          <LintPanel items={lint} />
        </TabsContent>
        <TabsContent value="diffs">
          <DiffReview />
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default function StudioPage() {
  const text = useStudioStore((s) => s.text);
  const docType = useStudioStore((s) => s.docType);
  const mode = useStudioStore((s) => s.mode);
  const meta = useStudioStore((s) => s.meta);
  const setMeta = useStudioStore((s) => s.setMeta);
  const theme = useStudioStore((s) => s.theme);
  const logoFile = useStudioStore((s) => s.coverFile);
  const cornerFile = useStudioStore((s) => s.cornerFile);
  const sameForBoth = useStudioStore((s) => s.sameForBoth);
  const formatId = useStudioStore((s) => s.formatId);
  const brandGlow = useStudioStore((s) => s.brandGlow);
  const jobId = useStudioStore((s) => s.jobId);
  const documentId = useStudioStore((s) => s.documentId);
  const status = useStudioStore((s) => s.status);
  const progress = useStudioStore((s) => s.progress);
  const message = useStudioStore((s) => s.message);
  const preservedPct = useStudioStore((s) => s.preservedPct);
  const lint = useStudioStore((s) => s.lint);
  const isPressing = useStudioStore((s) => s.isPressing);
  const setJob = useStudioStore((s) => s.setJob);
  const brandPrimary = useThemeStore((s) => s.brandPrimary);
  const themeFromStore = useThemeStore((s) => s.theme);
  const [demoMode, setDemoMode] = useState(false);
  const [brandOpen, setBrandOpen] = useState(false);
  const [mobileTab, setMobileTab] = useState<"write" | "paper" | "brand">("write");
  const hydrate = useStudioStore((s) => s.hydrate);

  // Open in Studio: ?lib=<id> (Library) or ?template=<id> (sample notes)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const libId = params.get("lib");
    const templateId = params.get("template");
    if (!libId && !templateId) return;
    let cancelled = false;
    void (async () => {
      if (libId) {
        try {
          const doc = await getDoc(libId);
          if (cancelled) return;
          if (!doc) {
            toast.error("That document is no longer in your Library");
            return;
          }
          hydrate({
            text: doc.request.text,
            docType: doc.docType,
            mode: doc.mode,
            meta: doc.request.meta,
            theme: (doc.themeSnapshot as Theme | undefined) ?? null,
            coverFile: doc.request.logos?.cover
              ? new File([doc.request.logos.cover], "cover-logo", {
                  type: doc.request.logos.cover.type,
                })
              : null,
            cornerFile: doc.request.logos?.corner
              ? new File([doc.request.logos.corner], "corner-logo", {
                  type: doc.request.logos.corner.type,
                })
              : null,
            logoFlags: doc.request.logoFlags,
          });
          toast.success(`Opened “${doc.title}”`);
        } catch {
          toast.error("Could not open that document");
        }
      } else if (templateId) {
        const t = getTemplate(templateId);
        if (!t || cancelled) return;
        hydrate({
          text: t.text,
          docType: t.docType,
          mode: "format_only",
          meta: { title: t.title, version: "1.0", classification: "Internal" },
        });
      }
      window.history.replaceState(null, "", "/studio");
    })();
    return () => {
      cancelled = true;
    };
  }, [hydrate]);

  useEffect(() => {
    if (status === "done" && brandOpen) {
      requestAnimationFrame(() => {
        document.getElementById("studio-exports")?.scrollIntoView({
          behavior: "smooth",
          block: "nearest",
        });
      });
    }
  }, [status, brandOpen]);

  useJobStream({
    jobId: demoMode ? null : jobId,
    enabled: !!jobId && !demoMode,
    onEvent: (ev) => {
      setJob({
        status: ev.status,
        progress: ev.progress,
        message: ev.message,
        documentId: ev.document_id ?? undefined,
        preservedPct: ev.preserved_pct ?? null,
        // Only overwrite when the event carries lint/diffs (avoid wiping on early ticks)
        ...(ev.lint != null ? { lint: ev.lint } : {}),
        ...(ev.diffs != null ? { diffs: ev.diffs } : {}),
      });
    },
    onDone: (ev) => {
      const id = ev.document_id || jobId;
      setJob({
        isPressing: false,
        status: "done",
        documentId: id,
        preservedPct: ev.preserved_pct ?? 100,
        ...(ev.lint != null ? { lint: ev.lint } : {}),
        ...(ev.diffs != null ? { diffs: ev.diffs } : {}),
      });
      setBrandOpen(true);
      setMobileTab("brand");
      announce("Document ready — downloads are open");
      toast.success("Press complete — download DOCX or PDF from Brand & checks");
    },
    onError: (msg) => {
      // Don't wipe a completed job if a late SSE reconnect error arrives
      setJob({ isPressing: false, error: msg });
      if (status !== "done") {
        setJob({ status: "failed" });
        toast.error(msg);
      }
    },
  });

  const runDemoPress = useCallback(async () => {
    setDemoMode(true);
    setJob({
      isPressing: true,
      jobId: "demo",
      status: "queued",
      progress: 0,
      message: "Queued (demo press)",
      error: null,
      lint: [],
      diffs: [],
      preservedPct: null,
      documentId: null,
    });
    const steps = [
      { status: "theme" as const, progress: 0.12, message: "Extracting brand…" },
      { status: "ingest" as const, progress: 0.28, message: "Ingesting source spans…" },
      { status: "structure" as const, progress: 0.48, message: "Structuring blocks…" },
      { status: "verify" as const, progress: 0.68, message: "Verifying content lock…" },
      { status: "render_docx" as const, progress: 0.84, message: "Rendering DOCX…" },
      { status: "render_pdf" as const, progress: 0.94, message: "Rendering PDF…" },
      {
        status: "done" as const,
        progress: 1,
        message: "Ready",
        preservedPct: mode === "format_only" ? 100 : 96.4,
      },
    ];
    for (const step of steps) {
      await new Promise((r) => setTimeout(r, 420));
      setJob({
        status: step.status,
        progress: step.progress,
        message: step.message,
        preservedPct: step.preservedPct ?? null,
        // Keep null so ExportBar refuses fake downloads
        documentId: null,
        lint:
          step.status === "verify" || step.status === "done"
            ? [
                {
                  level: "info",
                  code: "A11Y_TABLE_HEADER",
                  message: "Tables include header rows",
                },
                {
                  level: "info",
                  code: "CONTRAST_AA",
                  message: "Theme pairs meet WCAG AA",
                },
              ]
            : [],
        diffs:
          mode === "improve" && step.status === "done"
            ? [
                {
                  block_id: "b-3",
                  before: "notify stakeholders asap",
                  after: "Notify stakeholders within 15 minutes.",
                  accepted: null,
                },
              ]
            : [],
      });
    }
    setJob({ isPressing: false });
    announce("Demo press complete");
    toast.success("Demo press complete — wire API for real downloads");
  }, [mode, setJob]);

  const runPress = useCallback(async () => {
    if (!text.trim()) {
      toast.error("Paste or type your notes first");
      setMobileTab("write");
      return;
    }
    setDemoMode(false);
    setJob({
      isPressing: true,
      error: null,
      lint: [],
      diffs: [],
      preservedPct: null,
      documentId: null,
      progress: 0,
      message: "Starting…",
      status: "queued",
    });
    try {
      const activeTheme =
        theme ?? themeFromStore ?? buildFallbackTheme(brandPrimary);
      const job = await createDocument({
        text,
        doc_type: docType,
        mode,
        meta,
        theme: activeTheme,
        formatId,
        logoCover: logoFile,
        logoCorner: sameForBoth ? logoFile : cornerFile,
        force_rules: true,
      });
      setJob({
        jobId: job.id,
        documentId: job.document_id ?? job.id,
        status: job.status,
        message: job.message,
      });
      announce("Job started");
      setMobileTab("paper");

      // Poll as backup if SSE events are missed
      const id = job.id;
      void (async () => {
        for (let i = 0; i < 90; i++) {
          await new Promise((r) => setTimeout(r, 1000));
          try {
            const j = await getJob(id);
            setJob({
              status: j.status,
              progress: j.progress,
              message: j.message,
              documentId: j.document_id ?? id,
              preservedPct: j.preserved_pct ?? null,
              ...(j.lint != null ? { lint: j.lint } : {}),
              ...(j.diffs != null ? { diffs: j.diffs } : {}),
            });
            if (j.status === "done") {
              setJob({
                isPressing: false,
                ...(j.lint != null ? { lint: j.lint } : {}),
                ...(j.diffs != null ? { diffs: j.diffs } : {}),
              });
              setBrandOpen(true);
              setMobileTab("brand");
              toast.success("Press complete — download DOCX or PDF from Brand & checks");
              return;
            }
            if (j.status === "failed") {
              setJob({ isPressing: false, error: j.error ?? "Job failed" });
              toast.error(j.error || "Job failed");
              return;
            }
          } catch {
            /* keep waiting */
          }
        }
      })();
    } catch (err) {
      console.error(err);
      toast.message("API unreachable — demo preview only (downloads disabled)");
      setMobileTab("paper");
      await runDemoPress();
    }
  }, [
    text,
    docType,
    mode,
    meta,
    theme,
    themeFromStore,
    logoFile,
    cornerFile,
    sameForBoth,
    formatId,
    brandPrimary,
    setJob,
    runDemoPress,
  ]);
  // setBrandOpen / setMobileTab are stable state setters — used inside poll/onDone

  const brandProps = {
    preservedPct,
    mode,
    documentId,
    status,
    lint,
  };

  return (
    <div className="relative mx-auto flex min-h-[calc(100dvh-3.5rem)] max-w-[1600px] flex-col px-3 py-3 lg:h-[calc(100dvh-3.5rem)] lg:min-h-0 lg:overflow-hidden sm:px-4">
      <AmbientGlow enabled={brandGlow} />
      <div className="relative z-10 flex min-h-0 flex-1 flex-col">
      {/* Slim toolbar */}
      <header className="mb-3 flex shrink-0 flex-wrap items-center gap-2 sm:gap-3">
        <input
          id="doc-title"
          value={meta.title}
          onChange={(e) => setMeta({ title: e.target.value })}
          className="min-w-[10rem] flex-1 rounded-[var(--radius-md)] border border-border bg-surface px-3 py-2 text-sm font-medium outline-none focus:border-brand sm:max-w-xs"
          placeholder="Document title"
          aria-label="Document title"
        />
        <FormatPicker compact />
        <ModeSwitch compact />
        <div className="ml-auto flex items-center gap-2">
          <Button
            type="button"
            variant="secondary"
            size="md"
            className="hidden lg:inline-flex"
            onClick={() => setBrandOpen((o) => !o)}
            aria-pressed={brandOpen}
          >
            <Palette size={16} weight="duotone" />
            Brand & checks
          </Button>
          <Button
            size="lg"
            onClick={() => void runPress()}
            loading={isPressing}
            disabled={isPressing}
          >
            <Printer size={18} weight="duotone" />
            Run press
          </Button>
        </div>
      </header>

      {/* Mobile tabs */}
      <div className="mb-3 flex shrink-0 gap-1 rounded-[var(--radius-md)] border border-border bg-surface p-1 lg:hidden">
        {(
          [
            ["write", "Write"],
            ["paper", "Paper"],
            ["brand", "Brand"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            onClick={() => setMobileTab(id)}
            className={cn(
              "flex-1 rounded-[calc(var(--radius-md)-2px)] px-3 py-2 text-sm font-medium transition-colors",
              mobileTab === id
                ? "bg-brand-tint text-brand"
                : "text-fg-muted hover:text-fg",
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Desktop: write | paper [| brand] */}
      <div
        className={cn(
          "hidden min-h-0 flex-1 gap-3 lg:grid",
          brandOpen ? "lg:grid-cols-[1fr_1fr_20rem]" : "lg:grid-cols-2",
        )}
      >
        <section className="relative z-10 flex min-h-0 flex-col gap-3 overflow-y-auto rounded-[var(--radius-lg)] border border-border bg-surface/60 p-3">
          <div className="shrink-0">
            <LogoPair />
          </div>
          <div className="flex min-h-0 flex-[2] flex-col">
            <TextInput />
          </div>
        </section>

        <section className="relative z-10 flex min-h-0 flex-col gap-3 overflow-hidden">
          <div className="min-h-0 flex-1 overflow-hidden rounded-[var(--radius-lg)] border border-border bg-surface/40 p-3">
            <PaperViewer />
          </div>
          <PressProgress status={status} progress={progress} message={message} />
        </section>

        {brandOpen ? (
          <aside className="relative z-10 min-h-0 overflow-hidden rounded-[var(--radius-lg)] border border-border bg-surface/60">
            <BrandPanel {...brandProps} onClose={() => setBrandOpen(false)} />
          </aside>
        ) : null}
      </div>

      {/* Mobile panes */}
      <div className="min-h-0 flex-1 lg:hidden">
        {mobileTab === "write" ? (
          <section className="flex h-full min-h-[60vh] flex-col gap-3 overflow-y-auto rounded-[var(--radius-lg)] border border-border bg-surface/60 p-3">
            <div className="shrink-0">
              <LogoPair />
            </div>
            <div className="flex min-h-0 flex-[2] flex-col">
              <TextInput />
            </div>
          </section>
        ) : null}
        {mobileTab === "paper" ? (
          <section className="flex h-full min-h-[60vh] flex-col gap-3">
            <div className="min-h-0 flex-1 overflow-hidden rounded-[var(--radius-lg)] border border-border bg-surface/40 p-3">
              <PaperViewer />
            </div>
            <PressProgress status={status} progress={progress} message={message} />
          </section>
        ) : null}
        {mobileTab === "brand" ? (
          <aside className="h-full min-h-[60vh] overflow-hidden rounded-[var(--radius-lg)] border border-border bg-surface/60">
            <BrandPanel {...brandProps} />
          </aside>
        ) : null}
      </div>
      </div>
    </div>
  );
}
