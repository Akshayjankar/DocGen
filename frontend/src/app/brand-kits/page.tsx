"use client";

import { Palette, Plus, Trash } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  createBrandKit,
  deleteBrandKit,
  listBrandKits,
} from "@/lib/api";
import { useThemeStore } from "@/lib/theme-store";
import type { Theme } from "@/types/api";

const DEMO_KITS = [
  {
    id: "demo-1",
    name: "Evergreen Ops",
    theme: {
      name: "Evergreen Ops",
      palette: {
        primary: "#1F6F5B",
        primary_dark: "#154A3D",
        primary_tint: "#E4F2ED",
        secondary: "#2C3A36",
        accent: "#C45C26",
        text: "#1A1714",
        muted: "#5C5348",
        surface: "#F6F2EA",
        info: "#175CD3",
        warning: "#B54708",
        success: "#067647",
        danger: "#B42318",
      },
      fonts: { heading: "Calibri", body: "Calibri", mono: "Consolas" },
      border: { style: "single" as const, width_pt: 1.5, color: "#1F6F5B", offset_pt: 24 },
      source: "preset" as const,
    },
  },
  {
    id: "demo-2",
    name: "Harbor Blue",
    theme: {
      name: "Harbor Blue",
      palette: {
        primary: "#1B4F72",
        primary_dark: "#12324A",
        primary_tint: "#E8F1F8",
        secondary: "#2C3E50",
        accent: "#B45309",
        text: "#1A1714",
        muted: "#5C5348",
        surface: "#F6F2EA",
        info: "#175CD3",
        warning: "#B54708",
        success: "#067647",
        danger: "#B42318",
      },
      fonts: { heading: "Calibri", body: "Calibri", mono: "Consolas" },
      border: { style: "double" as const, width_pt: 1.5, color: "#1B4F72", offset_pt: 24 },
      source: "preset" as const,
    },
  },
];

export default function BrandKitsPage() {
  const qc = useQueryClient();
  const setThemeFromApi = useThemeStore((s) => s.setThemeFromApi);
  const brandPrimary = useThemeStore((s) => s.brandPrimary);
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");

  const query = useQuery({
    queryKey: ["brand-kits"],
    queryFn: listBrandKits,
    retry: false,
  });

  const kits = query.isError || !query.data ? DEMO_KITS : query.data;

  const createMut = useMutation({
    mutationFn: async () => {
      const theme: Theme = {
        name,
        palette: {
          primary: brandPrimary,
          primary_dark: brandPrimary,
          primary_tint: "#E4F2ED",
          secondary: "#2C3A36",
          accent: "#C45C26",
          text: "#1A1714",
          muted: "#5C5348",
          surface: "#F6F2EA",
          info: "#175CD3",
          warning: "#B54708",
          success: "#067647",
          danger: "#B42318",
        },
        fonts: { heading: "Calibri", body: "Calibri", mono: "Consolas" },
        border: {
          style: "single",
          width_pt: 1.5,
          color: brandPrimary,
          offset_pt: 24,
        },
        source: "manual",
      };
      return createBrandKit(name, theme);
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["brand-kits"] });
      setOpen(false);
      setName("");
      toast.success("Brand kit saved");
    },
    onError: () => toast.message("API offline — kit kept locally for this session"),
  });

  const deleteMut = useMutation({
    mutationFn: deleteBrandKit,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["brand-kits"] });
      toast.success("Deleted");
    },
    onError: () => toast.error("Could not delete"),
  });

  return (
    <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-brand">
            Saved themes
          </p>
          <h1 className="mt-2 font-display text-4xl font-semibold tracking-tight">
            Brand kits
          </h1>
          <p className="mt-2 max-w-lg text-fg-muted">
            Reuse extracted palettes across documents. Kits store Theme only — never layout.
          </p>
        </div>
        <Button onClick={() => setOpen(true)}>
          <Plus size={16} weight="bold" />
          New kit
        </Button>
      </div>

      {query.isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2">
          <Skeleton className="h-36" />
          <Skeleton className="h-36" />
        </div>
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2">
          {kits.map((kit) => (
            <li
              key={kit.id}
              className="overflow-hidden rounded-[var(--radius-lg)] border border-border bg-surface"
            >
              <div
                className="h-20"
                style={{
                  background: `linear-gradient(120deg, ${kit.theme.palette.primary}, ${kit.theme.palette.accent})`,
                }}
              />
              <div className="flex items-start justify-between gap-3 p-4">
                <div>
                  <p className="flex items-center gap-2 font-medium">
                    <Palette size={16} className="text-brand" />
                    {kit.name}
                  </p>
                  <p className="mt-1 font-mono text-[11px] text-fg-muted">
                    {kit.theme.palette.primary}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => {
                      setThemeFromApi(kit.theme);
                      toast.success(`Applied ${kit.name}`);
                    }}
                  >
                    Apply
                  </Button>
                  {!kit.id.startsWith("demo-") ? (
                    <Button
                      size="sm"
                      variant="ghost"
                      aria-label={`Delete ${kit.name}`}
                      onClick={() => deleteMut.mutate(kit.id)}
                    >
                      <Trash size={16} />
                    </Button>
                  ) : null}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}

      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="Save brand kit"
        description="Uses the current Studio primary color."
      >
        <label className="block text-sm">
          Name
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 w-full rounded-[var(--radius-md)] border border-border bg-bg px-3 py-2"
            placeholder="Acme Compliance"
          />
        </label>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button
            disabled={!name.trim()}
            loading={createMut.isPending}
            onClick={() => createMut.mutate()}
          >
            Save
          </Button>
        </div>
      </Dialog>
    </div>
  );
}
