"use client";

import { DownloadSimple, FileDoc, FilePdf } from "@phosphor-icons/react";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/Button";
import { downloadUrl, exportPreview, previewPageUrl } from "@/lib/api";
import { saveDoc } from "@/lib/library-db";
import { useStudioStore } from "@/lib/studio-store";
import { cn } from "@/lib/cn";

type Format = "docx" | "pdf";

function isDemoId(id: string | null): boolean {
  return !id || id === "demo" || id === "demo-doc" || id.startsWith("demo");
}

async function fetchJobFile(documentId: string, format: Format): Promise<Blob> {
  const res = await fetch(downloadUrl(documentId, format));
  if (!res.ok) {
    let detail = "";
    try {
      detail = ((await res.json()) as { detail?: string }).detail || "";
    } catch {
      detail = await res.text().catch(() => "");
    }
    throw new Error(detail || `Download failed (${res.status})`);
  }
  return res.blob();
}

function saveBlob(blob: Blob, filename: string) {
  const a = document.createElement("a");
  const url = URL.createObjectURL(blob);
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function ExportBar({
  documentId,
  disabled,
}: {
  documentId: string | null;
  disabled?: boolean;
}) {
  const [busy, setBusy] = useState<Format | null>(null);
  const meta = useStudioStore((s) => s.meta);
  const text = useStudioStore((s) => s.text);
  const docType = useStudioStore((s) => s.docType);
  const mode = useStudioStore((s) => s.mode);
  const status = useStudioStore((s) => s.status);
  const preservedPct = useStudioStore((s) => s.preservedPct);
  const pageCount = useStudioStore((s) => s.pageCount);
  const previewId = useStudioStore((s) => s.previewId);
  const previewState = useStudioStore((s) => s.previewState);
  const theme = useStudioStore((s) => s.theme);
  const coverFile = useStudioStore((s) => s.coverFile);
  const cornerFile = useStudioStore((s) => s.cornerFile);
  const sameForBoth = useStudioStore((s) => s.sameForBoth);
  const cornerPosition = useStudioStore((s) => s.cornerPosition);
  const showCornerOnCover = useStudioStore((s) => s.showCornerOnCover);

  // Format-only exports come from the exact PreviewSession (what you see is
  // what you download); Improve exports come from the reviewed job document.
  const previewReady = !disabled && !!previewId && previewState === "exact";
  const jobReady =
    !disabled && status === "done" && !!documentId && !isDemoId(documentId);
  const source: "preview" | "job" | null =
    mode === "format_only" && previewReady ? "preview" : jobReady ? "job" : null;
  const ready = source !== null;

  const fetchFile = async (
    format: Format,
  ): Promise<{ blob: Blob; filename?: string }> =>
    source === "preview" && previewId
      ? exportPreview(previewId, format)
      : { blob: await fetchJobFile(documentId as string, format) };

  const persist = async (format: Format, blob: Blob) => {
    try {
      const otherFormat: Format = format === "pdf" ? "docx" : "pdf";
      const other = await fetchFile(otherFormat)
        .then((r) => r.blob)
        .catch(() => undefined);

      let thumbnail: Blob | undefined;
      if (source === "preview" && previewId) {
        thumbnail = await fetch(previewPageUrl(previewId, 1))
          .then((r) => (r.ok ? r.blob() : undefined))
          .catch(() => undefined);
      }

      const id = (source === "preview" ? previewId : documentId) as string;
      const saved = await saveDoc({
        id,
        createdAt: Date.now(),
        title: meta.title || "Untitled",
        docType,
        mode,
        pages: pageCount || 1,
        sealPct: preservedPct ?? (mode === "format_only" ? 100 : null),
        themeSnapshot: theme ?? undefined,
        request: {
          text,
          meta,
          logos: {
            cover: coverFile ?? undefined,
            corner: sameForBoth ? undefined : (cornerFile ?? undefined),
          },
          logoFlags: { sameForBoth, cornerPosition, showCornerOnCover },
        },
        files: {
          [format]: blob,
          [otherFormat]: other,
        },
        thumbnail,
      });
      if (saved) toast.success("Saved to Library");
    } catch {
      /* private mode / quota — download already succeeded */
    }
  };

  const open = async (format: Format) => {
    if (!ready) {
      toast.error("Nothing to export yet — add some text and wait for the paper to render");
      return;
    }
    setBusy(format);
    try {
      const { blob, filename } = await fetchFile(format);
      const safe = (meta.title || "Document").replace(/[^\w.-]+/g, "_");
      const date = meta.date || new Date().toISOString().slice(0, 10);
      saveBlob(blob, filename ?? `${safe}_v${meta.version || "1.0"}_${date}.${format}`);
      toast.success(`${format.toUpperCase()} downloaded`);
      await persist(format, blob);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Export failed — try again");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div
      id="studio-exports"
      className={cn(
        "flex flex-wrap items-center gap-2 rounded-[var(--radius-md)] border bg-surface p-3",
        ready ? "border-brand/50" : "border-border",
      )}
    >
      <DownloadSimple size={18} className="text-brand" weight="duotone" />
      <div className="mr-auto min-w-0">
        <p className="text-sm font-medium">Download</p>
        <p className="text-[11px] text-fg-muted">
          {ready
            ? source === "preview"
              ? "Exactly what the paper shows"
              : "DOCX and PDF are ready"
            : mode === "improve"
              ? "Available after press completes"
              : "Available once the paper is Exact"}
        </p>
      </div>
      <Button
        size="sm"
        variant="secondary"
        disabled={!ready || busy !== null}
        loading={busy === "docx"}
        onClick={() => void open("docx")}
      >
        <FileDoc size={16} />
        DOCX
      </Button>
      <Button
        size="sm"
        variant="primary"
        disabled={!ready || busy !== null}
        loading={busy === "pdf"}
        onClick={() => void open("pdf")}
      >
        <FilePdf size={16} />
        PDF
      </Button>
    </div>
  );
}
