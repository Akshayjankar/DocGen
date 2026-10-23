"use client";

import { create } from "zustand";
import type {
  DiffItem,
  DocType,
  DocumentMeta,
  JobStatus,
  LintItem,
  LogoAsset,
  Mode,
  Theme,
} from "@/types/api";

export type CornerAnchor = "corner" | "margin";
export type CornerPages = "all_except_cover" | "all" | "none";

export interface LogoFlagsPatch {
  sameForBoth?: boolean;
  cornerPosition?: "left" | "right";
  showCornerOnCover?: boolean;
  cornerAnchor?: CornerAnchor;
  cornerPages?: CornerPages;
  cornerHeightMm?: number;
}

interface StudioState {
  text: string;
  docType: DocType;
  formatId: string;
  mode: Mode;
  meta: DocumentMeta;
  logoFile: File | null;
  logoPreviewUrl: string | null;
  coverFile: File | null;
  coverPreviewUrl: string | null;
  coverAsset: LogoAsset | null;
  cornerFile: File | null;
  cornerPreviewUrl: string | null;
  cornerAsset: LogoAsset | null;
  sameForBoth: boolean;
  cornerPosition: "left" | "right";
  showCornerOnCover: boolean;
  cornerAnchor: CornerAnchor;
  cornerPages: CornerPages;
  cornerHeightMm: number;
  brandGlow: boolean;
  logosUsed: { cover: string | null; corner: string | null };
  touchedSettings: Record<string, true>;
  previewId: string | null;
  pageCount: number;
  previewState: "idle" | "draft" | "exact" | "error";
  theme: Theme | null;
  jobId: string | null;
  documentId: string | null;
  status: JobStatus | null;
  progress: number;
  message: string;
  preservedPct: number | null;
  lint: LintItem[];
  diffs: DiffItem[];
  error: string | null;
  isPressing: boolean;

  setText: (text: string) => void;
  setDocType: (docType: DocType) => void;
  setFormatId: (formatId: string) => void;
  setMode: (mode: Mode) => void;
  setMeta: (meta: Partial<DocumentMeta>) => void;
  setLogo: (file: File | null, previewUrl: string | null) => void;
  setCoverLogo: (
    file: File | null,
    previewUrl: string | null,
    asset: LogoAsset | null,
  ) => void;
  setCornerLogo: (
    file: File | null,
    previewUrl: string | null,
    asset: LogoAsset | null,
  ) => void;
  setLogoFlags: (flags: LogoFlagsPatch) => void;
  setBrandGlow: (enabled: boolean) => void;
  setPreview: (previewId: string | null, pageCount?: number) => void;
  setPreviewState: (state: "idle" | "draft" | "exact" | "error") => void;
  /** Replace document inputs (Library → Open in Studio, templates). */
  hydrate: (input: {
    text: string;
    docType: DocType;
    mode: Mode;
    meta: DocumentMeta;
    theme?: Theme | null;
    coverFile?: File | null;
    cornerFile?: File | null;
    formatId?: string;
    logoFlags?: LogoFlagsPatch;
    brandGlow?: boolean;
  }) => void;
  setTheme: (theme: Theme | null) => void;
  setJob: (
    partial: Partial<
      Pick<
        StudioState,
        | "jobId"
        | "documentId"
        | "status"
        | "progress"
        | "message"
        | "preservedPct"
        | "lint"
        | "diffs"
        | "error"
        | "isPressing"
      >
    >,
  ) => void;
  acceptDiff: (blockId: string) => void;
  rejectDiff: (blockId: string) => void;
  resetJob: () => void;
}

const defaultMeta: DocumentMeta = {
  title: "Untitled Document",
  version: "1.0",
  classification: "Internal",
};

function syncLegacyCornerPages(flags: LogoFlagsPatch): LogoFlagsPatch {
  const next = { ...flags };
  if (next.showCornerOnCover === true) {
    next.cornerPages = "all";
  } else if (next.showCornerOnCover === false && next.cornerPages === undefined) {
    /* keep existing cornerPages in merge */
  }
  if (next.cornerPages === "all") {
    next.showCornerOnCover = true;
  } else if (next.cornerPages === "all_except_cover" || next.cornerPages === "none") {
    next.showCornerOnCover = false;
  }
  return next;
}

function touchKeys(
  touched: Record<string, true>,
  flags: LogoFlagsPatch,
): Record<string, true> {
  const out = { ...touched };
  for (const key of Object.keys(flags) as (keyof LogoFlagsPatch)[]) {
    if (flags[key] !== undefined) out[key] = true;
  }
  return out;
}

export const useStudioStore = create<StudioState>((set) => ({
  text: "",
  docType: "sop",
  formatId: "sop",
  mode: "format_only",
  meta: defaultMeta,
  logoFile: null,
  logoPreviewUrl: null,
  coverFile: null,
  coverPreviewUrl: null,
  coverAsset: null,
  cornerFile: null,
  cornerPreviewUrl: null,
  cornerAsset: null,
  sameForBoth: false,
  cornerPosition: "left",
  showCornerOnCover: false,
  cornerAnchor: "corner",
  cornerPages: "all_except_cover",
  cornerHeightMm: 11,
  brandGlow: true,
  logosUsed: { cover: null, corner: null },
  touchedSettings: {},
  previewId: null,
  pageCount: 0,
  previewState: "idle",
  theme: null,
  jobId: null,
  documentId: null,
  status: null,
  progress: 0,
  message: "",
  preservedPct: null,
  lint: [],
  diffs: [],
  error: null,
  isPressing: false,

  setText: (text) => set({ text }),
  setDocType: (docType) => set({ docType, formatId: docType }),
  setFormatId: (formatId) =>
    set((s) => ({
      formatId,
      docType: formatId as DocType,
      touchedSettings: { ...s.touchedSettings, formatId: true },
    })),
  setMode: (mode) => set({ mode }),
  setMeta: (meta) => set((s) => ({ meta: { ...s.meta, ...meta } })),
  setLogo: (file, previewUrl) =>
    set({
      logoFile: file,
      logoPreviewUrl: previewUrl,
      coverFile: file,
      coverPreviewUrl: previewUrl,
    }),
  setCoverLogo: (file, previewUrl, asset) =>
    set((s) => ({
      coverFile: file,
      coverPreviewUrl: previewUrl,
      coverAsset: asset,
      logoFile: file,
      logoPreviewUrl: previewUrl,
      logosUsed: {
        ...s.logosUsed,
        cover: asset?.id ?? (file ? s.logosUsed.cover : null),
      },
    })),
  setCornerLogo: (file, previewUrl, asset) =>
    set((s) => ({
      cornerFile: file,
      cornerPreviewUrl: previewUrl,
      cornerAsset: asset,
      sameForBoth: false,
      logosUsed: {
        ...s.logosUsed,
        corner: asset?.id ?? (file ? s.logosUsed.corner : null),
      },
    })),
  setLogoFlags: (flags) =>
    set((s) => {
      const merged = syncLegacyCornerPages(flags);
      return {
        ...merged,
        touchedSettings: touchKeys(s.touchedSettings, merged),
      };
    }),
  setBrandGlow: (brandGlow) =>
    set((s) => ({
      brandGlow,
      touchedSettings: { ...s.touchedSettings, brandGlow: true },
    })),
  setPreview: (previewId, pageCount = 0) => set({ previewId, pageCount }),
  setPreviewState: (previewState) => set({ previewState }),
  hydrate: (input) =>
    set((s) => {
      for (const u of [s.coverPreviewUrl, s.cornerPreviewUrl]) {
        if (u?.startsWith("blob:")) URL.revokeObjectURL(u);
      }
      const cover = input.coverFile ?? null;
      const corner = input.cornerFile ?? null;
      const coverUrl = cover ? URL.createObjectURL(cover) : null;
      const cornerUrl = corner ? URL.createObjectURL(corner) : null;
      const lf = input.logoFlags ?? {};
      const cornerPages =
        lf.cornerPages ??
        (lf.showCornerOnCover ? "all" : "all_except_cover");
      const showCornerOnCover =
        lf.showCornerOnCover ?? cornerPages === "all";
      return {
        text: input.text,
        docType: input.docType,
        formatId: input.formatId ?? input.docType,
        mode: input.mode,
        meta: { ...defaultMeta, ...input.meta },
        theme: input.theme ?? null,
        coverFile: cover,
        coverPreviewUrl: coverUrl,
        coverAsset: null,
        logoFile: cover,
        logoPreviewUrl: coverUrl,
        cornerFile: corner,
        cornerPreviewUrl: cornerUrl,
        cornerAsset: null,
        sameForBoth: lf.sameForBoth ?? false,
        cornerPosition: lf.cornerPosition ?? "left",
        showCornerOnCover,
        cornerAnchor: lf.cornerAnchor ?? "corner",
        cornerPages,
        cornerHeightMm: lf.cornerHeightMm ?? 11,
        brandGlow: input.brandGlow ?? true,
        logosUsed: { cover: null, corner: null },
        touchedSettings: {},
        previewId: null,
        pageCount: 0,
        previewState: "idle",
        jobId: null,
        documentId: null,
        status: null,
        progress: 0,
        message: "",
        preservedPct: null,
        lint: [],
        diffs: [],
        error: null,
        isPressing: false,
      };
    }),
  setTheme: (theme) => set({ theme }),
  setJob: (partial) => set(partial),
  acceptDiff: (blockId) =>
    set((s) => ({
      diffs: s.diffs.map((d) =>
        d.block_id === blockId ? { ...d, accepted: true } : d,
      ),
    })),
  rejectDiff: (blockId) =>
    set((s) => ({
      diffs: s.diffs.map((d) =>
        d.block_id === blockId ? { ...d, accepted: false } : d,
      ),
    })),
  resetJob: () =>
    set({
      jobId: null,
      documentId: null,
      status: null,
      progress: 0,
      message: "",
      preservedPct: null,
      lint: [],
      diffs: [],
      error: null,
      isPressing: false,
    }),
}));
