"use client";

import { FileDoc, FilePdf, SealCheck } from "@phosphor-icons/react";
import { motion } from "motion/react";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { cn } from "@/lib/cn";

const floats = [
  {
    icon: FileDoc,
    label: "DOCX",
    sub: "Real styles · TOC field",
    x: "8%",
    y: "12%",
    delay: 0.2,
  },
  {
    icon: FilePdf,
    label: "PDF",
    sub: "Tagged · WCAG AA",
    x: "72%",
    y: "22%",
    delay: 0.35,
  },
  {
    icon: SealCheck,
    label: "Content Seal",
    sub: "100% preserved",
    x: "58%",
    y: "68%",
    delay: 0.5,
  },
];

export function FloatingDocs({ className }: { className?: string }) {
  const reduced = useReducedMotion();

  return (
    <div className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)}>
      {floats.map((f) => {
        const Icon = f.icon;
        return (
          <motion.div
            key={f.label}
            initial={reduced ? false : { opacity: 0, y: 20 }}
            animate={
              reduced
                ? { opacity: 1 }
                : { opacity: 1, y: [0, -10, 0] }
            }
            transition={
              reduced
                ? { delay: f.delay }
                : {
                    opacity: { delay: f.delay, duration: 0.5 },
                    y: {
                      delay: f.delay + 0.4,
                      duration: 4 + f.delay,
                      repeat: Infinity,
                      ease: "easeInOut",
                    },
                  }
            }
            className="absolute flex items-center gap-3 rounded-[var(--radius-md)] border border-border bg-surface/90 px-3 py-2 shadow-lg backdrop-blur-sm"
            style={{ left: f.x, top: f.y }}
          >
            <span className="flex size-9 items-center justify-center rounded-[var(--radius-sm)] bg-brand-tint text-brand">
              <Icon size={18} weight="duotone" />
            </span>
            <span>
              <span className="block text-sm font-medium leading-none">{f.label}</span>
              <span className="mt-1 block text-[11px] text-fg-muted">{f.sub}</span>
            </span>
          </motion.div>
        );
      })}
    </div>
  );
}
