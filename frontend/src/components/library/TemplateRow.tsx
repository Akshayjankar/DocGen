"use client";

import { FileDoc } from "@phosphor-icons/react";
import Link from "next/link";
import { TEMPLATES } from "@/lib/templates";

export function TemplateRow() {
  return (
    <section aria-labelledby="templates-heading" className="mt-16">
      <h2 id="templates-heading" className="font-display text-xl font-semibold">
        Start from a template
      </h2>
      <p className="mt-1 text-sm text-fg-muted">
        Sample notes that show off tables, callouts and code boxes.
      </p>
      <ul className="mt-6 grid gap-4 sm:grid-cols-3">
        {TEMPLATES.map((t) => (
          <li
            key={t.id}
            className="flex flex-col rounded-[var(--radius-lg)] border border-border bg-surface p-5"
          >
            <FileDoc size={28} weight="duotone" className="text-brand" />
            <h3 className="mt-4 font-display text-lg font-semibold">{t.title}</h3>
            <p className="mt-1 font-mono text-[11px] uppercase tracking-wider text-fg-muted">
              {t.docType.replace("_", " ")}
            </p>
            <p className="mt-3 flex-1 text-sm text-fg-muted">{t.blurb}</p>
            <Link
              href={`/studio?template=${t.id}`}
              className="mt-5 text-sm font-medium text-brand hover:underline"
            >
              Use in Studio →
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
