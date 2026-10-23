"use client";

import { Command } from "@phosphor-icons/react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "@/components/chrome/ThemeToggle";
import { cn } from "@/lib/cn";

const nav = [
  { href: "/studio", label: "Studio" },
  { href: "/brand-kits", label: "Brand kits" },
  { href: "/library", label: "Library" },
];

export function Header() {
  const pathname = usePathname();
  const studio = pathname?.startsWith("/studio");

  return (
    <header
      className={cn(
        "sticky top-0 z-40 border-b border-border/70 backdrop-blur-md",
        "bg-[var(--header-bg)]",
      )}
    >
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6">
        <Link
          href="/"
          className="group flex items-baseline gap-2"
          aria-label="Docgen home"
        >
          <span className="font-display text-lg font-semibold tracking-tight text-fg">
            Docgen
          </span>
          <span className="hidden font-serif text-sm italic text-fg-muted sm:inline">
            The Chroma Press
          </span>
        </Link>

        {!studio ? (
          <nav className="hidden items-center gap-1 md:flex" aria-label="Primary">
            {nav.map((item) => {
              const active = pathname === item.href || pathname?.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "rounded-[var(--radius-sm)] px-3 py-1.5 text-sm transition-colors",
                    active
                      ? "bg-brand-tint text-brand-dark font-medium"
                      : "text-fg-muted hover:text-fg",
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        ) : (
          <p className="hidden text-sm text-fg-muted sm:block">
            Three-pane press · Format-only by default
          </p>
        )}

        <div className="flex items-center gap-2">
          <kbd className="hidden items-center gap-1 rounded border border-border bg-surface px-1.5 py-0.5 font-mono text-[10px] text-fg-muted sm:inline-flex">
            <Command size={10} />K
          </kbd>
          <ThemeToggle />
          <Link
            href="/studio"
            className="inline-flex h-9 items-center rounded-[var(--radius-md)] bg-brand px-3 text-sm font-medium text-white hover:bg-brand-dark"
          >
            Open Studio
          </Link>
        </div>
      </div>
    </header>
  );
}
