"""End-to-end Phase 1 build pipeline (CLI / future jobs)."""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path

from app.models.blocks import Block
from app.models.document import DocType, DocumentMeta, RenderOptions
from app.models.theme import Theme
from app.services.ingest.parse import NormalizedText, parse_bytes, parse_text
from app.services.ingest.pii import redact
from app.services.renderer.docx_builder import build_docx
from app.services.renderer.pdf import ensure_pdf
from app.services.renderer.toc_pass import two_pass_toc
from app.services.structurer.rules import RulesStructurer
from app.services.theme_engine.extract import extract
from app.services.theme_engine.presets import get_preset
from app.services.verifier.content_lock import ContentLockResult, score
from app.services.verifier.docx_validate import DocxValidation
from app.services.verifier.docx_validate import check as validate_docx
from app.services.verifier.lint import LintIssue
from app.services.verifier.lint import run as lint_run


@dataclass
class BuildResult:
    docx_path: Path
    pdf_path: Path | None
    theme: Theme
    blocks: list[Block]
    normalized: NormalizedText
    content_lock: ContentLockResult
    lint: list[LintIssue]
    validation: DocxValidation


def build_document(
    *,
    text: str | None = None,
    text_path: Path | None = None,
    logo_path: Path | None = None,
    logo_bytes: bytes | None = None,
    out_dir: Path,
    doc_type: DocType = DocType.sop,
    mode: str = "format_only",
    meta: DocumentMeta | None = None,
    options: RenderOptions | None = None,
    theme: Theme | None = None,
    redact_pii: bool = False,
    skip_pdf: bool = False,
) -> BuildResult:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = meta or DocumentMeta()
    options = options or RenderOptions()

    # Theme
    if theme is None:
        if logo_bytes is None and logo_path is not None:
            logo_bytes = Path(logo_path).read_bytes()
        if logo_bytes:
            theme = extract(logo_bytes, name=meta.organization or "Brand")
            # Persist logo for cover
            logo_hash = hashlib.sha256(logo_bytes).hexdigest()[:16]
            saved_logo = out_dir / f"{logo_hash}.png"
            # Keep original bytes; cover can use logo_bytes directly.
            try:
                import io

                from PIL import Image

                img = Image.open(io.BytesIO(logo_bytes))
                if img.mode == "RGBA":
                    img.save(saved_logo, format="PNG")
                else:
                    img.convert("RGB").save(saved_logo, format="PNG")
                theme.logo_path = str(saved_logo)
            except Exception:
                raw = out_dir / f"{logo_hash}.bin"
                raw.write_bytes(logo_bytes)
        else:
            theme = get_preset("neutral")

    # Ingest
    if text is None and text_path is not None:
        data = Path(text_path).read_bytes()
        normalized = parse_bytes(data, filename=Path(text_path).name)
    elif text is not None:
        normalized = parse_text(text)
    else:
        raise ValueError("Provide text or text_path")

    if redact_pii or options.redact_pii:
        redacted, _mapping = redact(normalized.text)
        normalized = parse_text(redacted, language=normalized.language)

    # Structure (rules for Phase 1; LLM in Phase 2)
    structurer = RulesStructurer()
    blocks = structurer.structure(normalized, doc_type, mode=mode)  # type: ignore[arg-type]

    # Verify
    content_lock = score(normalized.text, blocks, mode=mode)
    lint = lint_run(blocks, doc_type, source=normalized.text)

    # Render
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in meta.title)[:60]
    docx_path = out_dir / f"{safe_title or 'document'}.docx"
    build_docx(
        source_text=normalized.text,
        blocks=blocks,
        theme=theme,
        meta=meta,
        options=options,
        out_path=docx_path,
        logo_bytes=logo_bytes,
        logo_path=theme.logo_path,
    )

    validation = validate_docx(docx_path)

    pdf_path: Path | None = None
    if not skip_pdf:
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
            )

    return BuildResult(
        docx_path=docx_path,
        pdf_path=pdf_path,
        theme=theme,
        blocks=blocks,
        normalized=normalized,
        content_lock=content_lock,
        lint=lint,
        validation=validation,
    )


def copy_logo_for_cover(logo_path: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(logo_path, dest)
    return dest
