"use client";

import { FileDoc, FilePdf, Trash } from "@phosphor-icons/react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import type { LibraryDoc } from "@/lib/library-db";

function useBlobUrl(blob: Blob | undefined): string | null {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    if (!blob) {
      setUrl(null);
      return;
    }
    const u = URL.createObjectURL(blob);
    setUrl(u);
    return () => URL.revokeObjectURL(u);
  }, [blob]);
  return url;
}

function safeName(title: string) {
  return (title || "document").replace(/[^\w.-]+/g, "_");
}

export function DocCard({
  doc,
  onDelete,
}: {
  doc: LibraryDoc;
  onDelete: (id: string) => void;
}) {
  const thumb = useBlobUrl(doc.thumbnail);

  const download = (blob: Blob, ext: "pdf" | "docx") => {
    const a = document.createElement("a");
    const url = URL.createObjectURL(blob);
    a.href = url;
    a.download = `${safeName(doc.title)}.${ext}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  return (
    <li className="flex flex-col overflow-hidden rounded-[var(--radius-lg)] border border-border bg-surface">
      <div className="aspect-[3/4] overflow-hidden bg-surface-2">
        {thumb ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={thumb}
            alt={`First page of ${doc.title}`}
            className="h-full w-full object-cover object-top"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-brand">
            <FileDoc size={40} weight="duotone" />
          </div>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-1 p-4">
        <h2 className="font-display text-base font-semibold leading-snug">{doc.title}</h2>
        <p className="font-mono text-[10px] uppercase tracking-wider text-fg-muted">
          {doc.docType.replace("_", " ")} · {doc.pages} {doc.pages === 1 ? "page" : "pages"}
          {doc.sealPct != null ? ` · Seal ${Math.round(doc.sealPct)}%` : ""}
        </p>
        <p className="text-xs text-fg-muted">
          {new Date(doc.createdAt).toLocaleDateString(undefined, {
            day: "numeric",
            month: "short",
            year: "numeric",
          })}
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {doc.files.docx ? (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => download(doc.files.docx as Blob, "docx")}
            >
              <FileDoc size={14} /> DOCX
            </Button>
          ) : null}
          {doc.files.pdf ? (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => download(doc.files.pdf as Blob, "pdf")}
            >
              <FilePdf size={14} /> PDF
            </Button>
          ) : null}
        </div>
        <div className="mt-2 flex items-center justify-between gap-2">
          <Link
            href={`/studio?lib=${encodeURIComponent(doc.id)}`}
            className="text-sm font-medium text-brand hover:underline"
          >
            Open in Studio →
          </Link>
          <button
            type="button"
            className="inline-flex items-center gap-1 rounded text-sm text-fg-muted hover:text-danger"
            onClick={() => onDelete(doc.id)}
            aria-label={`Delete ${doc.title}`}
          >
            <Trash size={14} /> Delete
          </button>
        </div>
      </div>
    </li>
  );
}
