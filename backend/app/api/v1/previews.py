"""Live paper preview = export session API (Revision 2/3)."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path

import pymupdf
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import get_settings
from app.models.blocks import Block
from app.models.document import DocType, DocumentMeta, RenderOptions
from app.models.theme import LogoAsset, LogoRole, LogoSet, Theme
from app.services.ingest.parse import parse_text
from app.services.preview.session import PreviewSession, new_preview_id, preview_store
from app.services.renderer.docx_builder import build_docx
from app.services.renderer.pdf import ensure_pdf
from app.services.structurer.rules import RulesStructurer
from app.services.theme_engine.extract import extract
from app.services.theme_engine.logo import process_logo, read_processed_bytes
from app.services.theme_engine.presets import get_preset

router = APIRouter(prefix="/previews", tags=["previews"])


class PageInfo(BaseModel):
    n: int
    png_url: str
    w: int
    h: int


class LogoUsed(BaseModel):
    id: str | None = None
    sha256: str | None = None


class LogosUsed(BaseModel):
    cover: LogoUsed = Field(default_factory=LogoUsed)
    corner: LogoUsed = Field(default_factory=LogoUsed)


class PreviewResponse(BaseModel):
    preview_id: str
    pages: list[PageInfo]
    blocks: list[Block]
    page_count: int
    warnings: list[str] = Field(default_factory=list)
    structured_by: str = "rules"
    duration_ms: float = 0.0
    theme: Theme | None = None
    meta: DocumentMeta | None = None
    logos_used: LogosUsed = Field(default_factory=LogosUsed)
    format_id: str | None = None


def _sha(data: bytes | None) -> str | None:
    if not data:
        return None
    return hashlib.sha256(data).hexdigest()


def _asset_used(asset: LogoAsset | None, data: bytes | None) -> LogoUsed:
    return LogoUsed(id=asset.id if asset else None, sha256=_sha(data))


def _pdf_to_pngs(pdf_path: Path, out_dir: Path, dpi: int = 110) -> list[tuple[Path, int, int]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(pdf_path)
    pages: list[tuple[Path, int, int]] = []
    zoom = dpi / 72.0
    mat = pymupdf.Matrix(zoom, zoom)
    for i in range(doc.page_count):
        pix = doc[i].get_pixmap(matrix=mat, alpha=False)
        dest = out_dir / f"page-{i + 1}.png"
        pix.save(str(dest))
        pages.append((dest, pix.width, pix.height))
    doc.close()
    return pages


def _build_session(
    *,
    text: str,
    meta: DocumentMeta,
    options: RenderOptions,
    theme: Theme,
    logo_bytes: bytes | None,
    corner_bytes: bytes | None,
    structured_by: str = "rules",
    format_id: str | None = None,
    doc_type: DocType = DocType.sop,
) -> PreviewSession:
    t0 = time.perf_counter()
    settings = get_settings()
    preview_id = new_preview_id()
    work = Path(settings.data_dir) / "previews" / preview_id
    work.mkdir(parents=True, exist_ok=True)

    normalized = parse_text(text)
    blocks = RulesStructurer().structure(normalized, doc_type=doc_type)
    cover_sha = _sha(logo_bytes) or _sha(read_processed_bytes(theme.logos.cover))
    corner_sha = _sha(corner_bytes) or _sha(read_processed_bytes(theme.logos.corner))
    cache_key = hashlib.sha256(
        f"{normalized.text}|{cover_sha}|{corner_sha}|{theme.logos.model_dump_json()}|{format_id}".encode()
    ).hexdigest()

    docx_path = work / "preview.docx"
    build_docx(
        source_text=normalized.text,
        blocks=blocks,
        theme=theme,
        meta=meta,
        options=options,
        out_path=docx_path,
        logo_bytes=logo_bytes,
    )
    pdf_path = ensure_pdf(
        docx_path,
        out_dir=work,
        source_text=normalized.text,
        blocks=blocks,
        theme=theme,
        meta=meta,
        logo_bytes=logo_bytes,
        corner_bytes=corner_bytes,
    )
    pngs = _pdf_to_pngs(pdf_path, work / "pages", dpi=110)
    duration = (time.perf_counter() - t0) * 1000

    session = PreviewSession(
        id=preview_id,
        source_text=normalized.text,
        blocks=blocks,
        theme=theme,
        meta=meta,
        options=options,
        structured_by=structured_by,
        docx_path=docx_path,
        pdf_path=pdf_path,
        page_pngs=[p for p, _, _ in pngs],
        duration_ms=duration,
        text_hash=cache_key,
    )
    session.warnings = []
    preview_store.create(session)
    for path, w, h in pngs:
        path.with_suffix(".meta").write_text(f"{w}x{h}")
    return session


def _to_response(session: PreviewSession, *, format_id: str | None = None) -> PreviewResponse:
    pages: list[PageInfo] = []
    for i, path in enumerate(session.page_pngs):
        meta_f = path.with_suffix(".meta")
        w, h = 800, 1130
        if meta_f.exists():
            try:
                w_s, h_s = meta_f.read_text().split("x")
                w, h = int(w_s), int(h_s)
            except Exception:
                pass
        pages.append(
            PageInfo(
                n=i + 1,
                png_url=f"/api/v1/previews/{session.id}/pages/{i + 1}.png",
                w=w,
                h=h,
            )
        )
    cover_data = read_processed_bytes(session.theme.logos.cover)
    corner_data = read_processed_bytes(session.theme.logos.corner)
    if session.theme.logos.same_for_both and not corner_data:
        corner_data = cover_data
    return PreviewResponse(
        preview_id=session.id,
        pages=pages,
        blocks=session.blocks,
        page_count=len(pages),
        warnings=session.warnings,
        structured_by=session.structured_by,
        duration_ms=session.duration_ms,
        theme=session.theme,
        meta=session.meta,
        logos_used=LogosUsed(
            cover=_asset_used(session.theme.logos.cover, cover_data),
            corner=_asset_used(session.theme.logos.corner, corner_data),
        ),
        format_id=format_id,
    )


@router.post("", response_model=PreviewResponse)
async def create_preview(
    text: str = Form(""),
    title: str = Form("Untitled Document"),
    version: str = Form("1.0"),
    author: str = Form(""),
    classification: str = Form("Internal"),
    date: str = Form(""),
    format_id: str | None = Form(None),
    logo: UploadFile | None = File(None),
    logo_cover: UploadFile | None = File(None),
    logo_corner: UploadFile | None = File(None),
    corner_logo: UploadFile | None = File(None),
    theme_json: str | None = Form(None),
) -> PreviewResponse:
    meta = DocumentMeta(
        title=title,
        version=version,
        author=author,
        classification=classification,
        date=date or DocumentMeta().date,
    )
    options = RenderOptions()
    # Prefer explicit role keys; keep legacy `logo` / `corner_logo`
    cover_upload = logo_cover or logo
    corner_upload = logo_corner or corner_logo
    logo_bytes = await cover_upload.read() if cover_upload else None
    corner_bytes = await corner_upload.read() if corner_upload else None

    if theme_json:
        theme = Theme.model_validate_json(theme_json)
    elif logo_bytes:
        theme = extract(logo_bytes, name=meta.organization or "Brand")
    else:
        theme = get_preset("neutral")

    settings = get_settings()
    logos_dir = Path(settings.data_dir) / "logos"
    incoming = theme.logos or LogoSet()
    logos = LogoSet(
        cover=incoming.cover,
        corner=incoming.corner,
        same_for_both=bool(incoming.same_for_both),
        corner_position=incoming.corner_position,
        corner_anchor=getattr(incoming, "corner_anchor", "corner"),
        corner_pages=getattr(incoming, "corner_pages", "all_except_cover"),
        corner_height_mm=getattr(incoming, "corner_height_mm", 11.0),
        show_corner_on_cover=incoming.show_corner_on_cover,
        palette_source=incoming.palette_source,
    )
    if logo_bytes:
        cover, _ = process_logo(logo_bytes, role=LogoRole.cover, out_dir=logos_dir)
        logos.cover = cover
        theme.logo_path = cover.processed_path
        if logos.same_for_both and not corner_bytes:
            logos.corner = cover
    if corner_bytes:
        corner, _ = process_logo(corner_bytes, role=LogoRole.corner, out_dir=logos_dir)
        logos.corner = corner
        logos.same_for_both = False
    theme.logos = logos

    doc_type = DocType.sop
    if format_id:
        aliases = {
            "notes": DocType.memo,
            "minutes": DocType.meeting_minutes,
        }
        try:
            doc_type = DocType(format_id)
        except ValueError:
            doc_type = aliases.get(format_id, DocType.sop)
        from app.services.formats.apply import apply_preset
        from app.services.formats.registry import get_preset as get_format_preset

        preset = get_format_preset(format_id) or get_format_preset(doc_type.value)
        if preset:
            theme, options = apply_preset(preset, theme, options)

    session = _build_session(
        text=text or " ",
        meta=meta,
        options=options,
        theme=theme,
        logo_bytes=logo_bytes,
        corner_bytes=corner_bytes,
        format_id=format_id,
        doc_type=doc_type,
    )
    return _to_response(session, format_id=format_id)


class PreviewPatch(BaseModel):
    text: str | None = None
    meta: DocumentMeta | None = None
    options: RenderOptions | None = None
    theme: Theme | None = None
    format_id: str | None = None


@router.patch("/{preview_id}", response_model=PreviewResponse)
async def patch_preview(preview_id: str, body: PreviewPatch) -> PreviewResponse:
    session = preview_store.get(preview_id)
    if not session:
        raise HTTPException(404, "Preview not found")
    text = body.text if body.text is not None else session.source_text
    meta = body.meta or session.meta
    options = body.options or session.options
    theme = body.theme or session.theme
    format_id = body.format_id
    if format_id:
        from app.services.formats.apply import apply_preset
        from app.services.formats.registry import get_preset as get_format_preset

        preset = get_format_preset(format_id)
        if preset:
            theme, options = apply_preset(preset, theme, options)
    logo_bytes = read_processed_bytes(theme.logos.cover)
    corner_bytes = read_processed_bytes(theme.logos.corner)
    if theme.logos.same_for_both and logo_bytes and not corner_bytes:
        corner_bytes = logo_bytes
    new_session = _build_session(
        text=text,
        meta=meta,
        options=options,
        theme=theme,
        logo_bytes=logo_bytes,
        corner_bytes=corner_bytes,
        structured_by=session.structured_by,
        format_id=format_id,
    )
    preview_store.delete(new_session.id)
    new_session.id = preview_id
    preview_store.create(new_session)
    return _to_response(new_session, format_id=body.format_id)


@router.get("/{preview_id}/pages/{n}.png")
async def get_page_png(preview_id: str, n: int) -> FileResponse:
    session = preview_store.get(preview_id)
    if not session:
        raise HTTPException(404, "Preview not found")
    if n < 1 or n > len(session.page_pngs):
        raise HTTPException(404, "Page not found")
    return FileResponse(session.page_pngs[n - 1], media_type="image/png")


@router.post("/{preview_id}/export")
async def export_preview(preview_id: str, format: str = "pdf") -> FileResponse:
    session = preview_store.get(preview_id)
    if not session:
        raise HTTPException(404, "Preview not found")
    fmt = format.lower()
    if fmt == "pdf":
        if not session.pdf_path or not session.pdf_path.exists():
            raise HTTPException(500, "PDF missing")
        name = f"{session.meta.title}_v{session.meta.version}_{session.meta.date}.pdf".replace(
            " ", "_"
        )
        return FileResponse(session.pdf_path, media_type="application/pdf", filename=name)
    if fmt == "docx":
        if not session.docx_path or not session.docx_path.exists():
            raise HTTPException(500, "DOCX missing")
        name = f"{session.meta.title}_v{session.meta.version}_{session.meta.date}.docx".replace(
            " ", "_"
        )
        return FileResponse(
            session.docx_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=name,
        )
    raise HTTPException(400, "format must be pdf|docx")
