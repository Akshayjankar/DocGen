"use client";

import { Moon, Sun } from "@phosphor-icons/react";
import { useTheme } from "next-themes";
import { useCallback, useEffect, useState } from "react";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { circularReveal } from "@/lib/motion";
import { cn } from "@/lib/cn";

export function ThemeToggle({ className }: { className?: string }) {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const reduced = useReducedMotion();

  useEffect(() => setMounted(true), []);

  const toggle = useCallback(
    (e: React.MouseEvent<HTMLButtonElement>) => {
      const next = resolvedTheme === "dark" ? "light" : "dark";
      const x = e.clientX;
      const y = e.clientY;
      circularReveal(x, y, reduced);

      const go = () => setTheme(next);

      if (
        !reduced &&
        typeof document !== "undefined" &&
        "startViewTransition" in document
      ) {
        (
          document as Document & {
            startViewTransition: (cb: () => void) => void;
          }
        ).startViewTransition(go);
      } else {
        go();
      }
    },
    [resolvedTheme, setTheme, reduced],
  );

  if (!mounted) {
    return (
      <button
        type="button"
        aria-label="Toggle theme"
        className={cn(
          "inline-flex size-9 items-center justify-center rounded-full border border-border bg-surface",
          className,
        )}
      />
    );
  }

  const isDark = resolvedTheme === "dark";

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isDark ? "Switch to Paper (light)" : "Switch to Darkroom"}
      title={isDark ? "Paper" : "Darkroom"}
      className={cn(
        "inline-flex size-9 items-center justify-center rounded-full border border-border bg-surface text-fg transition-colors hover:bg-surface-2",
        className,
      )}
    >
      {isDark ? <Sun size={18} weight="duotone" /> : <Moon size={18} weight="duotone" />}
    </button>
  );
}
