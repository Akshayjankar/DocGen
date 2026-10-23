"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function Footer() {
  const pathname = usePathname();
  if (pathname?.startsWith("/studio")) return null;

  return (
    <footer className="relative z-10 border-t border-border/70">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-10 sm:flex-row sm:items-end sm:justify-between sm:px-6">
        <div>
          <div className="flex items-center gap-2.5">
            <span aria-hidden className="h-5 w-1 rounded-full bg-brand" />
            <p className="font-display text-lg font-semibold tracking-tight">Docgen</p>
          </div>
          <p className="mt-2 max-w-sm font-serif text-sm italic text-fg-muted">
            Rough notes in. Compliance-grade, on-brand documents out — wording locked.
          </p>
        </div>
        <nav
          className="flex flex-wrap gap-x-5 gap-y-2 text-sm text-fg-muted"
          aria-label="Footer"
        >
          <Link href="/privacy" className="hover:text-fg">
            Privacy
          </Link>
          <Link href="/studio" className="hover:text-fg">
            Studio
          </Link>
          <Link href="/library" className="hover:text-fg">
            Library
          </Link>
        </nav>
      </div>
      <div className="border-t border-border/50">
        <p className="mx-auto max-w-7xl px-4 py-3 font-mono text-[11px] text-fg-muted sm:px-6">
          APP_NAME = &quot;Docgen&quot; · LLM never owns layout · WCAG AA by construction
        </p>
      </div>
    </footer>
  );
}
