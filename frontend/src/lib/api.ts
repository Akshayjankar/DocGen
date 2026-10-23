import type {
  BrandKit,
  DocumentRequest,
  HealthResponse,
  Job,
  LogoRole,
  LogoUploadResponse,
  DocumentMeta,
  PreviewPatchBody,
  PreviewResponse,
  Theme,
} from "@/types/api";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function parseJson<T>(res: Response): Promise<T> {
  const text = await res.text();
  if (!text) return {} as T;
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new ApiError("Invalid JSON response", res.status, text);
  }
}

async function request<T>(
  path: string,
  init?: RequestInit & { formData?: FormData },
): Promise<T> {
  const { formData, headers, ...rest } = init ?? {};
  const res = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: formData
      ? headers
      : {
          "Content-Type": "application/json",
          ...headers,
        },
    body: formData ?? rest.body,
  });

  if (!res.ok) {
    let body: unknown;
    try {
      body = await res.json();
    } catch {
      body = await res.text();
    }
    throw new ApiError(
      typeof body === "object" && body && "detail" in body
        ? String((body as { detail: unknown }).detail)
        : `Request failed (${res.status})`,
      res.status,
      body,
    );
  }

  if (res.status === 204) return undefined as T;
  return parseJson<T>(res);
}

/** POST /api/v1/themes/extract — logo or docx → Theme */
export async function extractTheme(file: File): Promise<Theme> {
  const form = new FormData();
  form.append("logo", file);
  return request<Theme>("/api/v1/themes/extract", {
    method: "POST",
    formData: form,
  });
}

/** POST /api/v1/documents — multipart create generation job */
export async function createDocument(
  payload: DocumentRequest & {
    logo?: File | null;
    logoCover?: File | null;
    logoCorner?: File | null;
    cornerLogo?: File | null;
    formatId?: string | null;
    force_rules?: boolean;
  },
): Promise<Job> {
  const form = new FormData();
  form.append("text", payload.text);
  form.append("doc_type", payload.doc_type);
  form.append("mode", payload.mode);
  form.append("force_rules", payload.force_rules ? "true" : "false");
  if (payload.formatId) form.append("format_id", payload.formatId);
  if (payload.meta) form.append("meta", JSON.stringify(payload.meta));
  if (payload.options) form.append("options", JSON.stringify(payload.options));
  if (payload.theme) form.append("theme", JSON.stringify(payload.theme));
  const cover = payload.logoCover ?? payload.logo;
  const corner = payload.logoCorner ?? payload.cornerLogo;
  if (cover) {
    form.append("logo", cover);
    form.append("logo_cover", cover);
  }
  if (corner) {
    form.append("corner_logo", corner);
    form.append("logo_corner", corner);
  }

  const res = await request<{ job_id: string; document_id: string }>(
    "/api/v1/documents",
    { method: "POST", formData: form },
  );
  return {
    id: res.job_id,
    status: "queued",
    progress: 0,
    message: "Queued",
    document_id: res.document_id,
  };
}

/** SSE endpoint URL for job events */
export function jobEventsUrl(jobId: string): string {
  return `${API_BASE}/api/v1/jobs/${jobId}/events`;
}

/** GET /api/v1/documents/{id}/download?format=docx|pdf */
export function downloadUrl(
  documentId: string,
  format: "docx" | "pdf" = "docx",
): string {
  return `${API_BASE}/api/v1/documents/${documentId}/download?format=${format}`;
}

export async function getJob(jobId: string): Promise<Job> {
  return request<Job>(`/api/v1/jobs/${jobId}`);
}

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/api/v1/health");
}

export async function listBrandKits(): Promise<BrandKit[]> {
  const rows = await request<
    Array<{
      id: string;
      name: string;
      theme_json?: Theme;
      theme?: Theme;
      created_at?: string;
      updated_at?: string;
    }>
  >("/api/v1/brand-kits");
  return rows.map((r) => ({
    id: r.id,
    name: r.name,
    theme: (r.theme_json || r.theme || {}) as Theme,
    created_at: r.created_at,
    updated_at: r.updated_at,
  }));
}

export async function getBrandKit(id: string): Promise<BrandKit> {
  const r = await request<{
    id: string;
    name: string;
    theme_json?: Theme;
    created_at?: string;
    updated_at?: string;
  }>(`/api/v1/brand-kits/${id}`);
  return {
    id: r.id,
    name: r.name,
    theme: (r.theme_json || {}) as Theme,
    created_at: r.created_at,
    updated_at: r.updated_at,
  };
}

export async function createBrandKit(
  name: string,
  theme: Theme,
): Promise<BrandKit> {
  const r = await request<{
    id: string;
    name: string;
    theme_json?: Theme;
  }>("/api/v1/brand-kits", {
    method: "POST",
    body: JSON.stringify({ name, theme }),
  });
  return { id: r.id, name: r.name, theme: (r.theme_json || theme) as Theme };
}

export async function updateBrandKit(
  id: string,
  patch: { name?: string; theme?: Theme },
): Promise<BrandKit> {
  const r = await request<{
    id: string;
    name: string;
    theme_json?: Theme;
  }>(`/api/v1/brand-kits/${id}`, {
    method: "PUT",
    body: JSON.stringify(patch),
  });
  return {
    id: r.id,
    name: r.name,
    theme: (r.theme_json || patch.theme || {}) as Theme,
  };
}

export async function deleteBrandKit(id: string): Promise<void> {
  return request<void>(`/api/v1/brand-kits/${id}`, { method: "DELETE" });
}

/* ── Revision 2: logos + live preview sessions ─────────────────────── */

export interface UploadLogoOptions {
  role?: LogoRole;
  bgTolerance?: number;
  altText?: string;
  removeBg?: boolean;
  extractPalette?: boolean;
  maxWidthMm?: number;
  maxHeightMm?: number;
}

/** POST /api/v1/logos — process a logo (bg removal, sizing) + palette theme */
export async function uploadLogo(
  file: File,
  opts: UploadLogoOptions = {},
): Promise<LogoUploadResponse> {
  const form = new FormData();
  form.append("logo", file);
  form.append("role", opts.role ?? "cover");
  form.append("bg_tolerance", String(opts.bgTolerance ?? 10));
  form.append("alt_text", opts.altText ?? "Company logo");
  form.append("remove_bg", opts.removeBg === false ? "false" : "true");
  form.append("extract_palette", opts.extractPalette === false ? "false" : "true");
  if (opts.maxWidthMm != null) form.append("max_width_mm", String(opts.maxWidthMm));
  if (opts.maxHeightMm != null) form.append("max_height_mm", String(opts.maxHeightMm));
  return request<LogoUploadResponse>("/api/v1/logos", {
    method: "POST",
    formData: form,
  });
}

export interface CreatePreviewInput {
  text: string;
  meta: DocumentMeta;
  logo?: File | null;
  logoCover?: File | null;
  cornerLogo?: File | null;
  logoCorner?: File | null;
  formatId?: string | null;
  theme?: Theme | null;
  signal?: AbortSignal;
}

/** POST /api/v1/previews — build a PreviewSession (DOCX + PDF + page PNGs) */
export async function createPreview(
  input: CreatePreviewInput,
): Promise<PreviewResponse> {
  const form = new FormData();
  form.append("text", input.text);
  form.append("title", input.meta.title || "Untitled Document");
  form.append("version", input.meta.version ?? "1.0");
  form.append("author", input.meta.author ?? "");
  form.append("classification", input.meta.classification ?? "Internal");
  if (input.meta.date) form.append("date", input.meta.date);
  if (input.theme) form.append("theme_json", JSON.stringify(input.theme));
  if (input.formatId) form.append("format_id", input.formatId);
  const cover = input.logoCover ?? input.logo;
  const corner = input.logoCorner ?? input.cornerLogo;
  if (cover) {
    form.append("logo", cover);
    form.append("logo_cover", cover);
  }
  if (corner) {
    form.append("corner_logo", corner);
    form.append("logo_corner", corner);
  }
  return request<PreviewResponse>("/api/v1/previews", {
    method: "POST",
    formData: form,
    signal: input.signal,
  });
}

/** PATCH /api/v1/previews/{id} — rebuild the session in place */
export async function patchPreview(
  id: string,
  body: PreviewPatchBody,
  signal?: AbortSignal,
): Promise<PreviewResponse> {
  return request<PreviewResponse>(`/api/v1/previews/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
    signal,
  });
}

/** Absolute URL of a rendered page PNG. */
export function previewPageUrl(id: string, n: number): string {
  return `${API_BASE}/api/v1/previews/${id}/pages/${n}.png`;
}

/** POST /api/v1/previews/{id}/export — returns the file blob + suggested name */
export async function exportPreview(
  id: string,
  format: "pdf" | "docx" = "pdf",
): Promise<{ blob: Blob; filename: string }> {
  const res = await fetch(`${API_BASE}/api/v1/previews/${id}/export?format=${format}`, {
    method: "POST",
  });
  if (!res.ok) {
    let detail = "";
    try {
      detail = ((await res.json()) as { detail?: string }).detail ?? "";
    } catch {
      /* ignore */
    }
    throw new ApiError(detail || `Export failed (${res.status})`, res.status);
  }
  const cd = res.headers.get("content-disposition") ?? "";
  const m = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(cd);
  const rawName = m?.[1];
  const filename = rawName
    ? decodeURIComponent(rawName)
    : `docgen-${id.slice(0, 8)}.${format}`;
  return { blob: await res.blob(), filename };
}
