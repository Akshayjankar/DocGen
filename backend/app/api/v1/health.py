from __future__ import annotations

from fastapi import APIRouter

from app import APP_NAME, __version__
from app.config import get_settings
from app.services.renderer.pdf import find_soffice
from app.services.structurer.providers.router import provider_status

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, object]:
    settings = get_settings()
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": __version__,
        "pdf_engine": settings.pdf_engine,
        "libreoffice": bool(find_soffice()),
        "providers": provider_status(),
    }
