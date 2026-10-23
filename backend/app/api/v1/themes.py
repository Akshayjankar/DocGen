from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import get_settings
from app.models.theme import Theme
from app.services.job_runner import extract_theme_from_upload
from app.services.theme_engine.presets import get_preset, list_presets

router = APIRouter(prefix="/themes", tags=["themes"])


@router.post("/extract", response_model=Theme)
async def extract_theme(logo: UploadFile = File(...)) -> Theme:
    settings = get_settings()
    data = await logo.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(413, "File too large")
    name = logo.filename or "logo.png"
    # magic-ish check
    if not (
        data[:8].startswith(b"\x89PNG")
        or data[:3] == b"\xff\xd8\xff"
        or data[:4] in (b"GIF8", b"RIFF")
        or b"<svg" in data[:200].lower()
        or data[:2] == b"PK"  # docx
    ):
        raise HTTPException(400, "Unsupported file type")
    return await extract_theme_from_upload(data, name)


@router.get("/presets")
def presets() -> dict[str, list[str]]:
    return {"presets": list_presets()}


@router.get("/presets/{name}", response_model=Theme)
def preset(name: str) -> Theme:
    return get_preset(name)
