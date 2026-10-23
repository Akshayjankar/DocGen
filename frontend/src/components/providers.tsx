"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import { useEffect, useState, type ReactNode } from "react";
import { Toaster } from "sonner";
import { useBrandVars } from "@/hooks/useBrandVars";
import { CommandPalette } from "@/components/chrome/CommandPalette";
import { Cursor } from "@/components/chrome/Cursor";
import { Grain } from "@/components/chrome/Grain";

function BrandSync({ children }: { children: ReactNode }) {
  useBrandVars();
  return <>{children}</>;
}

function SmoothScroll({ children }: { children: ReactNode }) {
  useEffect(() => {
    let lenis: { destroy: () => void; raf: (t: number) => void } | null = null;
    let raf = 0;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) return;

    void import("lenis").then(({ default: Lenis }) => {
      lenis = new Lenis({
        duration: 1.1,
        smoothWheel: true,
      });
      document.documentElement.classList.add("lenis", "lenis-smooth");
      const loop = (time: number) => {
        lenis?.raf(time);
        raf = requestAnimationFrame(loop);
      };
      raf = requestAnimationFrame(loop);
    });

    return () => {
      cancelAnimationFrame(raf);
      lenis?.destroy();
      document.documentElement.classList.remove("lenis", "lenis-smooth");
    };
  }, []);

  return <>{children}</>;
}

export function Providers({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      }),
  );

  return (
    <ThemeProvider
      attribute="data-theme"
      defaultTheme="light"
      enableSystem
      disableTransitionOnChange
      themes={["light", "dark"]}
    >
      <QueryClientProvider client={client}>
        <BrandSync>
          <SmoothScroll>
            <Grain />
            <Cursor />
            <CommandPalette />
            {children}
            <Toaster
              theme="system"
              position="bottom-right"
              toastOptions={{
                className:
                  "!bg-surface !text-fg !border-border !font-[family-name:var(--font-sans)]",
              }}
            />
          </SmoothScroll>
        </BrandSync>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
