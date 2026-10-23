/** Frontend API contracts mirroring backend Pydantic models. */

export type HexColor = string;

export type DocType =
  | "sop"
  | "report"
  | "setup_guide"
  | "release_notes"
  | "proposal"
  | "policy"
  | "meeting_minutes"
  | "memo";

export type Mode = "format_only" | "improve";

export type JobStatus =
  | "queued"
  | "theme"
  | "ingest"
  | "structure"
  | "verify"
  | "render_docx"
  | "render_pdf"
  | "done"
  | "failed";

export interface Palette {
  primary: HexColor;
  primary_dark: HexColor;
  primary_tint: HexColor;
  secondary: HexColor;
  accent: HexColor;
  text: HexColor;
  muted: HexColor;
  surface: HexColor;
  info: HexColor;
  warning: HexColor;
  success: HexColor;
  danger: HexColor;
}

export interface FontPair {
  heading: string;
  body: string;
  mono: string;
}

export interface BorderSpec {
  style: "none" | "hairline" | "single" | "double" | "thick-thin" | "art-line";
  width_pt: number;
  color: HexColor;
  offset_pt: number;
}

export interface ContrastPair {
  foreground: HexColor;
  background: HexColor;
  ratio: number;
  aa: boolean;
  aaa: boolean;
  label: string;
}

export interface ContrastReport {
  pairs: ContrastPair[];
  all_aa: boolean;
  adjustments: string[];
}

export type LogoRole = "cover" | "corner";

export interface LogoAsset {
  id: string;
  role: LogoRole;
  filename: string;
  mime: string;
  width_px: number;
  height_px: number;
  aspect: number;
  original_path: string;
  processed_path: string;
  background: "none" | "was_transparent" | "removed" | "kept";
  bg_tolerance: number;
  max_width_mm: number;
  max_height_mm: number;
  alt_text: string;
  warnings: string[];
}

export interface LogoSet {
  cover?: LogoAsset | null;
  corner?: LogoAsset | null;
  same_for_both: boolean;
  corner_position: "left" | "right";
  corner_anchor?: "corner" | "margin";
  corner_pages?: "all_except_cover" | "all" | "none";
  corner_height_mm?: number;
  show_corner_on_cover: boolean;
  palette_source: "cover" | "corner" | "both";
}

export interface LayoutSpec {
  page_size: "a4" | "letter";
  margin_left_mm: number;
  margin_right_mm: number;
  margin_top_mm: number;
  margin_bottom_mm: number;
  cover_style: "centered" | "editorial" | "minimal";
  border_style: "none" | "hairline" | "single" | "double";
  force_title_uppercase: boolean;
}

export interface Theme {
  name: string;
  palette: Palette;
  fonts: FontPair;
  border: BorderSpec;
  logos?: LogoSet;
  layout?: LayoutSpec;
  logo_path?: string | null;
  logo_alt?: string;
  contrast?: ContrastReport;
  source?: "logo" | "docx" | "url" | "preset" | "manual";
}

export interface DocumentMeta {
  title: string;
  version?: string;
  author?: string;
  approver?: string;
  reviewed_by?: string;
  approved_by?: string;
  document_id?: string;
  classification?: string;
  date?: string;
  subtitle?: string;
  organization?: string;
  subject?: string;
}

export interface RenderOptions {
  cover?: boolean;
  toc?: boolean | "auto";
  revision_history?: boolean | "auto";
  border?: boolean;
  watermark?: boolean;
  classification_label?: boolean;
  redact_pii?: boolean;
  page_numbers?: boolean;
  cover_style?: "centered" | "editorial" | "minimal";
}

export interface DocumentRequest {
  text: string;
  doc_type: DocType;
  mode: Mode;
  theme?: Theme | null;
  brand_kit_id?: string | null;
  meta?: DocumentMeta;
  options?: RenderOptions;
}

export interface Job {
  id: string;
  status: JobStatus;
  progress: number;
  message: string;
  error?: string | null;
  document_id?: string | null;
  preserved_pct?: number | null;
  lint?: LintItem[];
  diffs?: DiffItem[];
  extras?: Record<string, unknown>;
}

export interface JobEvent {
  status: JobStatus;
  progress: number;
  message: string;
  document_id?: string | null;
  preserved_pct?: number | null;
  error?: string | null;
  lint?: LintItem[];
  diffs?: DiffItem[];
}

/** Backend emits `severity`; older UI used `level` — accept both. */
export interface LintItem {
  level?: "info" | "warning" | "error";
  severity?: "info" | "warning" | "error";
  code: string;
  message: string;
  block_id?: string | null;
}

export interface DiffItem {
  block_id: string;
  before: string;
  after: string;
  accepted?: boolean | null;
}

export interface BrandKit {
  id: string;
  name: string;
  theme: Theme;
  created_at?: string;
  updated_at?: string;
}

export interface HealthResponse {
  status: string;
  app?: string;
  version?: string;
  pdf_engine?: string;
  libreoffice?: boolean;
}

export interface LogoUploadResponse {
  asset: LogoAsset;
  palette_theme?: Theme | null;
}

export interface PreviewPage {
  n: number;
  png_url: string;
  w: number;
  h: number;
}

export interface PreviewResponse {
  preview_id: string;
  pages: PreviewPage[];
  page_count: number;
  warnings: string[];
  structured_by: string;
  duration_ms: number;
  theme?: Theme | null;
  meta?: DocumentMeta | null;
}

export interface PreviewPatchBody {
  text?: string;
  meta?: DocumentMeta;
  options?: RenderOptions;
  theme?: Theme;
}
