from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.deps import DbDep
from app.models.db import BrandKit, utcnow

router = APIRouter(prefix="/brand-kits", tags=["brand-kits"])


@router.get("")
def list_kits(db: DbDep) -> list[BrandKit]:
    return list(db.exec(select(BrandKit)).all())


@router.post("")
def create_kit(body: dict[str, Any], db: DbDep) -> BrandKit:
    kit = BrandKit(
        id=uuid4().hex,
        name=body.get("name") or "Untitled kit",
        logo_path=body.get("logo_path"),
        theme_json=body.get("theme") or body.get("theme_json") or {},
        footer=body.get("footer") or "",
        classification=body.get("classification") or "Internal",
    )
    db.add(kit)
    db.commit()
    db.refresh(kit)
    return kit


@router.get("/{kit_id}")
def get_kit(kit_id: str, db: DbDep) -> BrandKit:
    kit = db.get(BrandKit, kit_id)
    if not kit:
        raise HTTPException(404, "Not found")
    return kit


@router.put("/{kit_id}")
def update_kit(kit_id: str, body: dict[str, Any], db: DbDep) -> BrandKit:
    kit = db.get(BrandKit, kit_id)
    if not kit:
        raise HTTPException(404, "Not found")
    if "name" in body:
        kit.name = body["name"]
    if "theme" in body:
        kit.theme_json = body["theme"]
    if "theme_json" in body:
        kit.theme_json = body["theme_json"]
    if "footer" in body:
        kit.footer = body["footer"]
    if "classification" in body:
        kit.classification = body["classification"]
    kit.updated_at = utcnow()
    db.add(kit)
    db.commit()
    db.refresh(kit)
    return kit


@router.delete("/{kit_id}")
def delete_kit(kit_id: str, db: DbDep) -> dict[str, bool]:
    kit = db.get(BrandKit, kit_id)
    if not kit:
        raise HTTPException(404, "Not found")
    db.delete(kit)
    db.commit()
    return {"ok": True}
