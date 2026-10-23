import type { Transition, Variants } from "motion/react";

/** Shared motion presets — respect reduced motion via CSS / hooks. */

export const easeOutExpo: Transition = {
  duration: 0.55,
  ease: [0.16, 1, 0.3, 1],
};

export const springSoft: Transition = {
  type: "spring",
  stiffness: 280,
  damping: 28,
};

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0, transition: easeOutExpo },
};

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { duration: 0.4 } },
};

export const staggerChildren: Variants = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.08, delayChildren: 0.06 },
  },
};

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.94 },
  show: { opacity: 1, scale: 1, transition: springSoft },
};

/** Circular view-transition clip for theme toggle. */
export function circularReveal(
  x: number,
  y: number,
  prefersReducedMotion: boolean,
): void {
  if (prefersReducedMotion || typeof document === "undefined") return;
  const root = document.documentElement;
  if (!("startViewTransition" in document)) return;

  const endRadius = Math.hypot(
    Math.max(x, window.innerWidth - x),
    Math.max(y, window.innerHeight - y),
  );

  root.style.setProperty("--vt-x", `${x}px`);
  root.style.setProperty("--vt-y", `${y}px`);
  root.style.setProperty("--vt-r", `${endRadius}px`);
}
