"""DOCX companion PDF via native PyMuPDF (Jagrook-grade layout; LibreOffice optional)."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from app.config import get_settings
from app.models.blocks import Block
from app.models.document import DocumentMeta
from app.models.theme import Theme


class PdfConversionError(RuntimeError):
    pass


def find_soffice() -> str | None:
    settings = get_settings()
    candidates = [
        settings.soffice_path,
        "/usr/bin/soffice",
        "/usr/lib/libreoffice/program/soffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        shutil.which("soffice") or "",
        shutil.which("libreoffice") or "",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None


def convert_to_pdf(docx_path: Path, out_dir: Path | None = None, timeout: int | None = None) -> Path:
    """LibreOffice DOCX→PDF (optional engine only)."""
    soffice = find_soffice()
    if not soffice:
        raise PdfConversionError("LibreOffice (soffice) not found")

    settings = get_settings()
    timeout = timeout or settings.pdf_timeout_sec
    out_dir = out_dir or docx_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="docgen-lo-") as profile:
        cmd = [
            soffice,
            "--headless",
            "--norestore",
            "--nolockcheck",
            f"-env:UserInstallation=file://{profile}",
            "--convert-to",
            "pdf:writer_pdf_Export",
            "--outdir",
            str(out_dir),
            str(docx_path),
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise PdfConversionError(f"PDF conversion timed out after {timeout}s") from exc

        pdf_path = out_dir / (docx_path.stem + ".pdf")
        if not pdf_path.exists():
            raise PdfConversionError(
                f"PDF not produced. stdout={result.stdout!r} stderr={result.stderr!r}"
            )
        return pdf_path


def _native_pdf(
    *,
    out_path: Path,
    source_text: str,
    blocks: list[Block],
    theme: Theme,
    meta: DocumentMeta,
    logo_bytes: bytes | None,
    corner_bytes: bytes | None = None,
) -> Path:
    from app.services.renderer.pdf_native import render_pdf_from_blocks

    return render_pdf_from_blocks(
        out_path=out_path,
        source_text=source_text,
        blocks=blocks,
        theme=theme,
        meta=meta,
        logo_bytes=logo_bytes,
        corner_bytes=corner_bytes,
    )


def ensure_pdf(
    docx_path: Path,
    out_dir: Path | None = None,
    *,
    source_text: str | None = None,
    blocks: list[Block] | None = None,
    theme: Theme | None = None,
    meta: DocumentMeta | None = None,
    logo_bytes: bytes | None = None,
    corner_bytes: bytes | None = None,
) -> Path:
    """
    Default engine is native PyMuPDF (blocks + theme) — no LibreOffice required.
    Set PDF_ENGINE=libreoffice to convert the DOCX via soffice instead.
    """
    settings = get_settings()
    out_dir = out_dir or docx_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / (docx_path.stem + ".pdf")
    engine = (settings.pdf_engine or "native").strip().lower()
    meta = meta or DocumentMeta()

    can_native = source_text is not None and blocks is not None and theme is not None

    if engine == "native" and can_native:
        return _native_pdf(
            out_path=target,
            source_text=source_text,
            blocks=blocks,
            theme=theme,
            meta=meta,
            logo_bytes=logo_bytes,
            corner_bytes=corner_bytes,
        )

    if engine == "libreoffice":
        return convert_to_pdf(docx_path, out_dir=out_dir)

    # auto: native first, then LibreOffice, then last-resort text dump
    if can_native:
        return _native_pdf(
            out_path=target,
            source_text=source_text,
            blocks=blocks,
            theme=theme,
            meta=meta,
            logo_bytes=logo_bytes,
            corner_bytes=corner_bytes,
        )

    try:
        return convert_to_pdf(docx_path, out_dir=out_dir)
    except PdfConversionError:
        pass

    from app.services.renderer.pdf_native import render_pdf_from_docx_text_fallback

    return render_pdf_from_docx_text_fallback(docx_path, target)
