"use client";

import { Books, MagnifyingGlass } from "@phosphor-icons/react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { DocCard } from "@/components/library/DocCard";
import { StorageMeter } from "@/components/library/StorageMeter";
import { TemplateRow } from "@/components/library/TemplateRow";
import { Button } from "@/components/ui/Button";
import { useLibrary } from "@/hooks/useLibrary";

export default function LibraryPage() {
  const { docs, historyOn, bytes, ready, error, remove, clear, toggleHistory } =
    useLibrary();
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<"newest" | "title">("newest");

  const filtered = useMemo(() => {
    let list = docs;
    const needle = q.trim().toLowerCase();
    if (needle) {
      list = list.filter(
        (d) =>
          d.title.toLowerCase().includes(needle) ||
          d.docType.toLowerCase().includes(needle),
      );
    }
    if (sort === "title") list = [...list].sort((a, b) => a.title.localeCompare(b.title));
    return list;
  }, [docs, q, sort]);

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <h1 className="font-display text-4xl font-semibold tracking-tight">Library</h1>
      <p className="mt-3 max-w-xl text-fg-muted">
        Documents you export are kept in this browser only. Delete them anytime — nothing is
        stored on a server.
      </p>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-4 rounded-[var(--radius-md)] border border-border bg-surface px-4 py-3 text-sm">
        <label className="inline-flex cursor-pointer items-center gap-2 text-fg-muted">
          <input
            type="checkbox"
            className="accent-[var(--brand)]"
            checked={historyOn}
            onChange={(e) => void toggleHistory(e.target.checked)}
          />
          Save exports to this browser
        </label>
        <StorageMeter bytes={bytes} count={docs.length} className="flex-1 sm:max-w-xs" />
        {docs.length > 0 ? (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              if (confirm("Delete all saved documents from this browser?")) void clear();
            }}
          >
            Clear all
          </Button>
        ) : null}
      </div>

      {error ? (
        <p
          role="alert"
          className="mt-4 rounded-[var(--radius-md)] border border-border bg-surface px-4 py-3 text-sm text-fg-muted"
        >
          {error}
        </p>
      ) : null}

      {docs.length > 0 ? (
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <label className="relative min-w-[200px] flex-1">
            <span className="sr-only">Search documents</span>
            <MagnifyingGlass
              size={16}
              className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-fg-muted"
            />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search by title or type…"
              className="w-full rounded-[var(--radius-md)] border border-border bg-surface py-2 pr-3 pl-9 text-sm outline-none focus:border-brand"
            />
          </label>
          <select
            aria-label="Sort documents"
            value={sort}
            onChange={(e) => setSort(e.target.value as "newest" | "title")}
            className="rounded-[var(--radius-md)] border border-border bg-surface px-3 py-2 text-sm"
          >
            <option value="newest">Newest</option>
            <option value="title">Title A–Z</option>
          </select>
        </div>
      ) : null}

      {!ready ? (
        <p className="mt-10 text-sm text-fg-muted">Loading…</p>
      ) : docs.length === 0 ? (
        <div className="mt-12 flex flex-col items-center gap-3 rounded-[var(--radius-lg)] border border-dashed border-border px-6 py-12 text-center">
          <Books size={40} weight="duotone" className="text-brand" />
          <p className="font-display text-lg">Your library is empty</p>
          <p className="max-w-sm text-sm text-fg-muted">
            Export a DOCX or PDF from Studio and it will show up here, with a thumbnail and
            its Content Seal score.
          </p>
          <Link href="/studio" className="mt-1 text-sm font-medium text-brand hover:underline">
            Open Studio →
          </Link>
        </div>
      ) : filtered.length === 0 ? (
        <p className="mt-10 text-sm text-fg-muted">No documents match “{q}”.</p>
      ) : (
        <ul className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((d) => (
            <DocCard key={d.id} doc={d} onDelete={(id) => void remove(id)} />
          ))}
        </ul>
      )}

      <TemplateRow />
    </div>
  );
}
