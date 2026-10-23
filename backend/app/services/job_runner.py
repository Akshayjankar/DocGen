"""Background document generation pipeline with SSE progress."""

from __future__ import annotations

import json
from pathlib import Path

from app.models.document import DocType, DocumentMeta, JobStatus, RenderOptions
from app.models.theme import Theme
from app.services.diffing import block_diffs
from app.services.ingest.parse import parse_bytes, parse_text
from app.services.ingest.pii import redact
from app.services.jobs import JobRecord, job_store
from app.services.renderer.docx_builder import build_docx
from app.services.renderer.pdf import ensure_pdf
from app.services.renderer.toc_pass import two_pass_toc
from app.services.storage import get_storage
from app.services.structurer.llm import LLMStructurer
from app.services.structurer.rules import RulesStructurer
from app.services.theme_engine.extract import extract
from app.services.theme_engine.from_docx import from_docx
from app.services.theme_engine.presets import get_preset
from app.services.verifier.content_lock import score
from app.services.verifier.lint import run as lint_run


async def run_job(
    job: JobRecord,
    *,
    text: str | None,
    file_bytes: bytes | None,
    filename: str | None,
    logo_bytes: bytes | None,
    theme_json: str | None,
    doc_type: str,
    mode: str,
    meta_json: str | None,
    options_json: str | None,
    force_rules: bool = False,
    corner_bytes: bytes | None = None,
) -> None:
    storage = get_storage()
    out_dir = storage.job_dir(job.id)
    try:
        await job_store.emit(job, JobStatus.theme, 5, "Reading the logo…")
        theme: Theme
        if theme_json:
            theme = Theme.model_validate_json(theme_json)
        elif logo_bytes:
            theme = extract(logo_bytes, name="Brand")
            storage.save_bytes(job.id, logo_bytes, ".png")
        else:
            theme = get_preset("neutral")

        # Dual-logo processing (Revision 3 WP-A) — never mirror cover→corner unless same_for_both
        from app.models.theme import LogoRole, LogoSet
        from app.services.theme_engine.logo import process_logo

        logos_dir = out_dir / "logos"
        logos_dir.mkdir(parents=True, exist_ok=True)
        logos = theme.logos or LogoSet()
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
        job.theme = theme

        await job_store.emit(job, JobStatus.ingest, 20, "Tasting the colors… normalizing text")
        if file_bytes is not None and filename:
            normalized = parse_bytes(file_bytes, filename=filename)
        elif text is not None:
            normalized = parse_text(text)
        else:
            raise ValueError("No text provided")

        meta = DocumentMeta.model_validate_json(meta_json) if meta_json else DocumentMeta()
        options = (
            RenderOptions.model_validate_json(options_json) if options_json else RenderOptions()
        )
        job.meta = meta.model_dump()
        job.options = options.model_dump()
        job.mode = mode
        job.doc_type = doc_type

        if options.redact_pii:
            redacted, _ = redact(normalized.text)
            normalized = parse_text(redacted, language=normalized.language)

        job.source_text = normalized.text
        dt = DocType(doc_type)

        await job_store.emit(job, JobStatus.structure, 40, "Finding structure…")
        if force_rules or mode == "format_only":
            # Prefer rules for deterministic format_only; try LLM then fall back.
            structurer = LLMStructurer()
            if force_rules:
                blocks = RulesStructurer().structure(normalized, dt, mode=mode)  # type: ignore[arg-type]
                provider = "rules"
            else:
                try:
                    blocks = await structurer.structure(normalized, dt, mode=mode)  # type: ignore[arg-type]
                    provider = structurer.last_provider or "rules"
                except Exception:
                    blocks = RulesStructurer().structure(normalized, dt, mode=mode)  # type: ignore[arg-type]
                    provider = "rules"
        else:
            structurer = LLMStructurer()
            blocks = await structurer.structure(normalized, dt, mode=mode)  # type: ignore[arg-type]
            provider = structurer.last_provider or "rules"

        job.blocks = blocks
        job.meta["structured_by"] = provider
        if mode == "improve":
            job.diffs = block_diffs(normalized.text, blocks)

        await job_store.emit(job, JobStatus.verify, 55, "Checking content lock…")
        lock = score(normalized.text, blocks, mode=mode)
        job.preserved_pct = lock.preserved_pct
        job.lint = [i.__dict__ for i in lint_run(blocks, dt, source=normalized.text)]

        await job_store.emit(job, JobStatus.render_docx, 70, "Typesetting…")
        docx_path = out_dir / "document.docx"
        build_docx(
            source_text=normalized.text,
            blocks=blocks,
            theme=theme,
            meta=meta,
            options=options,
            out_path=docx_path,
            logo_bytes=logo_bytes,
        )
        job.docx_path = str(docx_path)
        job.document_id = job.id

        await job_store.emit(job, JobStatus.render_pdf, 85, "Binding PDF…")
        # Native PDF from blocks/theme (LibreOffice two-pass only if PDF_ENGINE=libreoffice)
        from app.config import get_settings

        pdf_path = None
        if get_settings().pdf_engine.strip().lower() == "libreoffice":
            pdf_path = two_pass_toc(docx_path, work_dir=out_dir)
        if pdf_path is None:
            pdf_path = ensure_pdf(
                docx_path,
                out_dir=out_dir,
                source_text=normalized.text,
                blocks=blocks,
                theme=theme,
                meta=meta,
                logo_bytes=logo_bytes,
                corner_bytes=corner_bytes,
            )
        job.pdf_path = str(pdf_path)

        await job_store.emit(job, JobStatus.done, 100, "Press complete")

        # Persist after done so on-disk status matches the live job
        (out_dir / "job.json").write_text(
            json.dumps(
                {
                    **job.to_public(),
                    "pdf_path": job.pdf_path,
                    "docx_path": job.docx_path,
                    "blocks": [b.model_dump() for b in blocks],
                    "theme": theme.model_dump(),
                    "diffs": job.diffs,
                    "lint": job.lint,
                    "structured_by": provider,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception as exc:  # noqa: BLE001
        job.error = str(exc)
        await job_store.emit(job, JobStatus.failed, job.progress, f"Failed: {exc}")
        try:
            from app.config import get_settings

            out = get_settings().data_dir / "jobs" / job.id
            if out.exists():
                (out / "job.json").write_text(
                    json.dumps({**job.to_public(), "error": job.error}, indent=2),
                    encoding="utf-8",
                )
        except Exception:
            pass


async def extract_theme_from_upload(data: bytes, filename: str) -> Theme:
    lower = filename.lower()
    if lower.endswith((".docx", ".dotx")):
        return from_docx(data)
    return extract(data, name=Path(filename).stem or "Brand")
