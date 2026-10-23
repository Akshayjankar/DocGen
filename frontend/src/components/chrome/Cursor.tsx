"use client";

import { useEffect, useState } from "react";
import { useReducedMotion } from "@/hooks/useReducedMotion";

/** Soft brand-tinted cursor follower — never visible outside the viewport. */
export function Cursor() {
  const reduced = useReducedMotion();
  const [pos, setPos] = useState({ x: -100, y: -100 });
  const [visible, setVisible] = useState(false);
  const [fine, setFine] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(pointer: fine)");
    setFine(mq.matches);
    const onMq = (e: MediaQueryListEvent) => setFine(e.matches);
    mq.addEventListener("change", onMq);
    return () => mq.removeEventListener("change", onMq);
  }, []);

  useEffect(() => {
    if (!fine || reduced) return;

    const hide = () => setVisible(false);

    const move = (e: MouseEvent) => {
      const inside =
        e.clientX >= 0 &&
        e.clientY >= 0 &&
        e.clientX <= window.innerWidth &&
        e.clientY <= window.innerHeight;
      if (!inside) {
        hide();
        return;
      }
      setPos({ x: e.clientX, y: e.clientY });
      setVisible(true);
    };

    const onDocOut = (e: MouseEvent) => {
      // relatedTarget null → left the document
      if (!e.relatedTarget) hide();
    };

    window.addEventListener("mousemove", move);
    window.addEventListener("blur", hide);
    document.documentElement.addEventListener("mouseleave", hide);
    document.addEventListener("mouseout", onDocOut);
    return () => {
      window.removeEventListener("mousemove", move);
      window.removeEventListener("blur", hide);
      document.documentElement.removeEventListener("mouseleave", hide);
      document.removeEventListener("mouseout", onDocOut);
    };
  }, [fine, reduced]);

  if (!fine || reduced) return null;

  return (
    <div
      aria-hidden
      className="pointer-events-none fixed z-[60] size-8 -translate-x-1/2 -translate-y-1/2 rounded-full border border-[color-mix(in_srgb,var(--brand)_55%,transparent)] transition-opacity duration-200"
      style={{
        left: pos.x,
        top: pos.y,
        opacity: visible ? 0.55 : 0,
        background:
          "radial-gradient(circle, color-mix(in srgb, var(--brand) 18%, transparent), transparent 70%)",
      }}
    />
  );
}
