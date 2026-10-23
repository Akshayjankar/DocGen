"use client";

import Link from "next/link";
import { motion } from "motion/react";
import { ArrowRight } from "@phosphor-icons/react";
import { ChromaDrop } from "@/components/hero/ChromaDrop";
import { FloatingDocs } from "@/components/hero/FloatingDocs";
import { PaperStack } from "@/components/hero/PaperStack";
import { BeforeAfterSlider } from "@/components/showcase/BeforeAfterSlider";
import { BrandGallery } from "@/components/showcase/BrandGallery";
import { Button } from "@/components/ui/Button";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { fadeUp, staggerChildren } from "@/lib/motion";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const reduced = useReducedMotion();
  const router = useRouter();

  return (
    <div>
      {/* Hero — one composition: brand, headline, support, CTA, dominant visual */}
      <section className="relative overflow-hidden">
        <FloatingDocs className="hidden lg:block" />
        <div className="relative mx-auto grid max-w-7xl gap-10 px-4 pt-14 pb-20 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:pt-20 lg:pb-28">
          <motion.div
            variants={reduced ? undefined : staggerChildren}
            initial={reduced ? false : "hidden"}
            animate="show"
            className="relative z-10"
          >
            <motion.p
              variants={fadeUp}
              className="font-mono text-[11px] uppercase tracking-[0.22em] text-brand"
            >
              The Chroma Press
            </motion.p>
            <motion.h1
              variants={fadeUp}
              className="mt-4 font-display text-5xl leading-[1.05] font-semibold tracking-tight text-fg sm:text-6xl lg:text-7xl"
            >
              Docgen
            </motion.h1>
            <motion.p
              variants={fadeUp}
              className="mt-5 max-w-md font-serif text-xl leading-snug text-fg-muted sm:text-2xl"
            >
              Rough notes in. On-brand SOPs out — wording locked.
            </motion.p>
            <motion.div variants={fadeUp} className="mt-8 flex flex-wrap gap-3">
              <Link href="/studio">
                <Button size="lg" variant="primary">
                  Open Studio
                  <ArrowRight size={18} weight="bold" />
                </Button>
              </Link>
              <Button
                size="lg"
                variant="secondary"
                onClick={() =>
                  document.getElementById("chroma-drop")?.scrollIntoView({
                    behavior: reduced ? "auto" : "smooth",
                  })
                }
              >
                Drop a logo
              </Button>
            </motion.div>
          </motion.div>

          <div className="relative z-10">
            <PaperStack />
          </div>
        </div>
      </section>

      <section
        id="chroma-drop"
        className="border-y border-border/70 bg-surface/40 py-16 sm:py-20"
      >
        <div className="mx-auto max-w-5xl px-4 sm:px-6">
          <ChromaDrop onReady={() => router.push("/studio")} />
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6">
        <div className="mb-10 max-w-xl">
          <h2 className="font-display text-3xl font-semibold tracking-tight">
            Before the press / after the press
          </h2>
          <p className="mt-2 text-fg-muted">
            Same words. Real Word styles, TOC field, striped tables, page X of Y.
          </p>
        </div>
        <BeforeAfterSlider />
      </section>

      <section className="border-t border-border/70 bg-surface/30 py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <div className="mb-10 max-w-xl">
            <h2 className="font-display text-3xl font-semibold tracking-tight">
              Sample brand inks
            </h2>
            <p className="mt-2 text-fg-muted">
              Click a swatch to re-tint the interface — the same path your logo takes.
            </p>
          </div>
          <BrandGallery />
        </div>
      </section>
    </div>
  );
}
