"use client";

import { ShieldCheck } from "@phosphor-icons/react";

export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-12 sm:px-6">
      <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-brand">
        Privacy first
      </p>
      <h1 className="mt-2 flex items-center gap-3 font-display text-4xl font-semibold tracking-tight">
        <ShieldCheck size={36} weight="duotone" className="text-brand" />
        Privacy
      </h1>
      <div className="prose-docgen mt-8 space-y-6 text-fg-muted">
        <p>
          Docgen is built so your operational text does not become someone else&apos;s
          training set by accident.
        </p>
        <ul className="list-disc space-y-3 pl-5">
          <li>
            <strong className="text-fg">No persistent text by default.</strong> Uploads
            and jobs TTL-delete (see <code className="font-mono text-sm">FILE_TTL_MINUTES</code>).
          </li>
          <li>
            <strong className="text-fg">Optional history</strong> is opt-in (
            <code className="font-mono text-sm">STORE_HISTORY</code>).
          </li>
          <li>
            <strong className="text-fg">PII redaction</strong> available in render options.
          </li>
          <li>
            <strong className="text-fg">Self-host path:</strong> set{" "}
            <code className="font-mono text-sm">LLM_PROVIDER=ollama</code> (or{" "}
            <code className="font-mono text-sm">none</code> for rules-only) so nothing leaves
            your network.
          </li>
          <li>
            <strong className="text-fg">No secrets in the frontend.</strong> Only{" "}
            <code className="font-mono text-sm">NEXT_PUBLIC_API_URL</code> is exposed.
          </li>
        </ul>
        <p className="rounded-[var(--radius-md)] border border-border bg-surface p-4 text-sm">
          Free cloud LLM tiers may train on prompts. Studio warns when Improve mode uses a
          cloud provider; choose Confidential → Ollama for sensitive drafts.
        </p>
      </div>
    </div>
  );
}
