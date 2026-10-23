from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.config import get_settings
from app.models.document import DocumentMeta, RenderOptions
from app.models.theme import Theme
from app.services.diffing import apply_diff_decisions
from app.services.job_runner import run_job
from app.services.jobs import job_store
from app.services.renderer.docx_builder import build_docx
from app.services.renderer.pdf import ensure_pdf
from app.services.storage import get_storage

router = APIRouter(tags=["documents"])


@router.post("/documents")
async def create_document(
    background: BackgroundTasks,
    text: str | None = Form(None),
    file: UploadFile | None = File(None),
    logo: UploadFile | None = File(None),
    logo_cover: UploadFile | None = File(None),
    logo_corner: UploadFile | None = File(None),
    corner_logo: UploadFile | None = File(None),
    doc_type: str = Form("sop"),
    format_id: str | None = Form(None),
    mode: str = Form("format_only"),
    meta: str | None = Form(None),
    options: str | None = Form(None),
    theme: str | None = Form(None),
    force_rules: bool = Form(False),
) -> dict[str, str]:
    settings = get_settings()
    max_bytes = settings.max_upload_mb * 1024 * 1024

    file_bytes = await file.read() if file else None
    if file_bytes and len(file_bytes) > max_bytes:
        raise HTTPException(413, "File too large")
    cover_upload = logo_cover or logo
    corner_upload = logo_corner or corner_logo
    logo_bytes = await cover_upload.read() if cover_upload else None
    corner_bytes = await corner_upload.read() if corner_upload else None
    if logo_bytes and len(logo_bytes) > max_bytes:
        raise HTTPException(413, "Logo too large")
    if corner_bytes and len(corner_bytes) > max_bytes:
        raise HTTPException(413, "Corner logo too large")

    if not text and not file_bytes:
        raise HTTPException(400, "Provide text or file")

    job = job_store.create()
    background.add_task(
        run_job,
        job,
        text=text,
        file_bytes=file_bytes,
        filename=file.filename if file else None,
        logo_bytes=logo_bytes,
        corner_bytes=corner_bytes,
        theme_json=theme,
        doc_type=format_id or doc_type,
        mode=mode,
        meta_json=meta,
        options_json=options,
        force_rules=force_rules,
    )
    return {"job_id": job.id, "document_id": job.id}


@router.get("/documents/{doc_id}/blocks")
def get_blocks(doc_id: str) -> dict[str, Any]:
    job = job_store.get(doc_id)
    if not job:
        raise HTTPException(404, "Not found")
    return {
        "blocks": [b.model_dump() for b in job.blocks],
        "diffs": job.diffs,
        "preserved_pct": job.preserved_pct,
        "lint": job.lint,
    }


@router.patch("/documents/{doc_id}/blocks")
async def patch_blocks(doc_id: str, body: dict[str, Any]) -> dict[str, Any]:
    job = job_store.get(doc_id)
    if not job or not job.docx_path:
        raise HTTPException(404, "Not found")

    decisions = body.get("decisions")  # {block_id: bool}
    overrides = body.get("overrides")  # [{id, type}]
    if decisions:
        job.blocks = apply_diff_decisions(job.source_text, job.blocks, decisions)
    if overrides:
        by_id = {b.id: b for b in job.blocks}
        for o in overrides:
            b = by_id.get(o.get("id"))
            if b and o.get("type"):
                b.type = o["type"]  # type: ignore[assignment]

    theme = job.theme or Theme.model_validate(
        json.loads(Path(get_storage().job_dir(doc_id) / "job.json").read_text()).get("theme")
    )
    meta = DocumentMeta.model_validate(job.meta) if job.meta else DocumentMeta()
    options = RenderOptions.model_validate(job.options) if job.options else RenderOptions()
    out = Path(job.docx_path)
    build_docx(
        source_text=job.source_text,
        blocks=job.blocks,
        theme=theme,
        meta=meta,
        options=options,
        out_path=out,
    )
    pdf = ensure_pdf(
        out,
        out_dir=out.parent,
        source_text=job.source_text,
        blocks=job.blocks,
        theme=theme,
        meta=meta,
    )
    job.pdf_path = str(pdf)
    return {"ok": True, "blocks": [b.model_dump() for b in job.blocks]}


@router.get("/documents/{doc_id}/download")
def download(doc_id: str, format: str = "docx") -> FileResponse:
    if doc_id in ("demo", "demo-doc") or doc_id.startswith("demo"):
        raise HTTPException(
            404,
            "Demo jobs have no downloadable file. Run press against the live API.",
        )
    job = job_store.get(doc_id)
    if not job:
        raise HTTPException(
            404,
            "Document not found (job expired or server restarted). Run press again.",
        )
    if format == "pdf":
        if not job.pdf_path or not Path(job.pdf_path).exists():
            raise HTTPException(
                404,
                "PDF not available — LibreOffice may be missing. Download DOCX instead.",
            )
        return FileResponse(
            job.pdf_path,
            media_type="application/pdf",
            filename=f"{doc_id}.pdf",
        )
    if not job.docx_path or not Path(job.docx_path).exists():
        raise HTTPException(404, "DOCX not available yet — wait for the job to finish")
    return FileResponse(
        job.docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{doc_id}.docx",
    )


@router.get("/documents/{doc_id}/preview")
def preview(doc_id: str) -> dict[str, Any]:
    job = job_store.get(doc_id)
    if not job:
        raise HTTPException(404, "Not found")
    # HTML-ish preview from blocks
    pages = []
    html_parts = []
    for b in job.blocks:
        text = b.resolved_text(job.source_text) if b.span else (b.text or "")
        if b.type == "heading":
            html_parts.append(f"<h{b.level or 1}>{text}</h{b.level or 1}>")
        elif b.type in ("callout_info", "callout_warning", "callout_success"):
            html_parts.append(f"<aside class='{b.type}'>{text}</aside>")
        elif b.type == "code":
            html_parts.append(f"<pre><code>{text}</code></pre>")
        else:
            html_parts.append(f"<p>{text}</p>")
    pages.append({"html": "\n".join(html_parts), "page": 1})
    return {"pages": pages, "theme": job.theme.model_dump() if job.theme else None}
