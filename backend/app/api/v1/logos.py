"""Logo upload / reprocess API (Revision 2 WP1)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import get_settings
from app.models.theme import LogoAsset, LogoRole, Theme
from app.services.theme_engine.extract import extract
from app.services.theme_engine.logo import process_logo

router = APIRouter(prefix="/logos", tags=["logos"])


class LogoResponse(BaseModel):
    asset: LogoAsset
    palette_theme: Theme | None = None


@router.post("", response_model=LogoResponse)
async def upload_logo(
    logo: UploadFile = File(...),
    role: str = Form("cover"),
    bg_tolerance: int = Form(10),
    max_width_mm: float | None = Form(None),
    max_height_mm: float | None = Form(None),
    alt_text: str = Form("Company logo"),
    remove_bg: bool = Form(True),
    extract_palette: bool = Form(True),
) -> LogoResponse:
    try:
        logo_role = LogoRole(role)
    except ValueError as exc:
        raise HTTPException(400, "role must be cover|corner") from exc
    data = await logo.read()
    if not data:
        raise HTTPException(400, "Empty file")
    settings = get_settings()
    out_dir = Path(settings.data_dir) / "logos"
    try:
        asset, _png = process_logo(
            data,
            role=logo_role,
            filename=logo.filename or "logo.png",
            out_dir=out_dir,
            bg_tolerance=bg_tolerance,
            max_width_mm=max_width_mm,
            max_height_mm=max_height_mm,
            alt_text=alt_text,
            remove_bg=remove_bg,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    theme = None
    if extract_palette:
        theme = extract(Path(asset.processed_path).read_bytes(), name="Logo")
        if logo_role == LogoRole.cover:
            theme.logos.cover = asset
        else:
            theme.logos.corner = asset
        theme.logo_path = asset.processed_path
        theme.logo_alt = asset.alt_text
        theme.source = "logo"
    return LogoResponse(asset=asset, palette_theme=theme)


class LogoPatch(BaseModel):
    bg_tolerance: int | None = None
    max_width_mm: float | None = None
    max_height_mm: float | None = None
    alt_text: str | None = None
    remove_bg: bool = True


@router.patch("/{logo_id}", response_model=LogoResponse)
async def reprocess_logo(logo_id: str, body: LogoPatch) -> LogoResponse:
    settings = get_settings()
    out_dir = Path(settings.data_dir) / "logos"
    orig = out_dir / f"{logo_id}_orig.bin"
    if not orig.exists():
        raise HTTPException(404, "Logo not found")
    data = orig.read_bytes()
    # Infer role from existing processed naming — default cover
    role = LogoRole.cover
    asset, _ = process_logo(
        data,
        role=role,
        filename=f"{logo_id}.png",
        out_dir=out_dir,
        bg_tolerance=body.bg_tolerance if body.bg_tolerance is not None else 10,
        max_width_mm=body.max_width_mm,
        max_height_mm=body.max_height_mm,
        alt_text=body.alt_text or "Company logo",
        remove_bg=body.remove_bg,
    )
    # Preserve id
    asset.id = logo_id
    return LogoResponse(asset=asset)
