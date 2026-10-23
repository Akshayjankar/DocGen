"""Deprecated alias — native PDF lives in pdf_native."""

from app.services.renderer.pdf_native import (  # noqa: F401
    render_pdf_from_blocks,
    render_pdf_from_docx_text_fallback,
)
