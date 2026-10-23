/** Accessibility helpers — WCAG AA focus and announcements. */

export function announce(message: string, politeness: "polite" | "assertive" = "polite"): void {
  if (typeof document === "undefined") return;
  let live = document.getElementById("docgen-live-region");
  if (!live) {
    live = document.createElement("div");
    live.id = "docgen-live-region";
    live.setAttribute("role", "status");
    live.setAttribute("aria-live", politeness);
    live.setAttribute("aria-atomic", "true");
    live.className = "sr-only";
    document.body.appendChild(live);
  }
  live.setAttribute("aria-live", politeness);
  live.textContent = "";
  // Force reflow so repeated messages are announced.
  void live.offsetWidth;
  live.textContent = message;
}

export function focusFirst(container: HTMLElement | null): void {
  if (!container) return;
  const el = container.querySelector<HTMLElement>(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
  );
  el?.focus();
}

export const KEY = {
  Escape: "Escape",
  Enter: "Enter",
  ArrowDown: "ArrowDown",
  ArrowUp: "ArrowUp",
  Slash: "/",
  k: "k",
} as const;
