"use client";

import { motion } from "motion/react";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { useThemeStore } from "@/lib/theme-store";
import { cn } from "@/lib/cn";

const sheets = [
  { rotate: -6, y: 18, label: "Cover" },
  { rotate: 2.5, y: 8, label: "TOC" },
  { rotate: -1, y: 0, label: "Body" },
];

export function PaperStack({ className }: { className?: string }) {
  const reduced = useReducedMotion();
  const brand = useThemeStore((s) => s.brandPrimary);

  return (
    <div
      className={cn("relative mx-auto h-[340px] w-full max-w-md", className)}
      aria-hidden
    >
      {sheets.map((sheet, i) => (
        <motion.div
          key={sheet.label}
          initial={reduced ? false : { opacity: 0, y: 40, rotate: sheet.rotate - 4 }}
          animate={{ opacity: 1, y: sheet.y, rotate: sheet.rotate }}
          transition={{ delay: 0.15 + i * 0.1, duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
          className="absolute inset-x-8 top-6 bottom-10 rounded-[2px] border border-black/10 bg-[#fffdf8] shadow-[0_20px_50px_-20px_rgba(0,0,0,0.35)]"
          style={{
            zIndex: i + 1,
            borderTop: `3px solid ${brand}`,
          }}
        >
          <div className="space-y-3 p-6">
            <div
              className="h-2 w-24 rounded-full"
              style={{ background: brand, opacity: 0.85 }}
            />
            <div className="h-2 w-3/4 rounded-full bg-black/10" />
            <div className="h-2 w-2/3 rounded-full bg-black/8" />
            <div className="mt-6 grid grid-cols-3 gap-2">
              {[0, 1, 2].map((c) => (
                <div
                  key={c}
                  className="h-8 rounded-sm"
                  style={{
                    background:
                      c === 0
                        ? brand
                        : c === 1
                          ? `color-mix(in srgb, ${brand} 35%, white)`
                          : "rgba(0,0,0,0.06)",
                  }}
                />
              ))}
            </div>
            <div className="mt-4 space-y-2">
              {[90, 78, 84, 60].map((w, idx) => (
                <div
                  key={idx}
                  className="h-1.5 rounded-full bg-black/8"
                  style={{ width: `${w}%` }}
                />
              ))}
            </div>
          </div>
          <span className="absolute right-4 bottom-3 font-mono text-[10px] tracking-wider text-black/30">
            {sheet.label}
          </span>
        </motion.div>
      ))}
    </div>
  );
}
