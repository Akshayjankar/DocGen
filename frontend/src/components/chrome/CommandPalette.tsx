"use client";

import {
  Books,
  House,
  Palette,
  ShieldCheck,
  SquaresFour,
} from "@phosphor-icons/react";
import { Command } from "cmdk";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { KEY } from "@/lib/a11y";

const links = [
  { href: "/", label: "Home", icon: House },
  { href: "/studio", label: "Studio", icon: SquaresFour },
  { href: "/brand-kits", label: "Brand kits", icon: Palette },
  { href: "/library", label: "Library", icon: Books },
  { href: "/privacy", label: "Privacy", icon: ShieldCheck },
];

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === KEY.k) {
        e.preventDefault();
        setOpen((o) => !o);
      }
      if (e.key === KEY.Escape) setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[70] flex items-start justify-center bg-black/40 px-4 pt-[18vh] backdrop-blur-sm">
      <button
        type="button"
        className="absolute inset-0 cursor-default"
        aria-label="Dismiss command palette"
        onClick={() => setOpen(false)}
      />
      <Command
        className="relative z-10 w-full max-w-lg overflow-hidden rounded-[var(--radius-lg)] border border-border bg-surface shadow-2xl"
        label="Command palette"
      >
        <Command.Input
          placeholder="Jump to… (⌘K)"
          className="w-full border-b border-border bg-transparent px-4 py-3 text-base outline-none placeholder:text-fg-muted"
          autoFocus
        />
        <Command.List className="max-h-72 overflow-auto p-2">
          <Command.Empty className="px-3 py-6 text-center text-sm text-fg-muted">
            No matches.
          </Command.Empty>
          <Command.Group heading="Navigate" className="px-1 py-1 text-xs text-fg-muted">
            {links.map(({ href, label, icon: Icon }) => (
              <Command.Item
                key={href}
                value={label}
                onSelect={() => {
                  setOpen(false);
                  router.push(href);
                }}
                className="flex cursor-pointer items-center gap-3 rounded-[var(--radius-md)] px-3 py-2 text-sm text-fg aria-selected:bg-brand-tint"
              >
                <Icon size={16} weight="duotone" className="text-brand" />
                {label}
              </Command.Item>
            ))}
          </Command.Group>
        </Command.List>
      </Command>
    </div>
  );
}
