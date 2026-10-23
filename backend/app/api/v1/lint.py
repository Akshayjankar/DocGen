from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.models.blocks import Block
from app.models.document import DocType
from app.services.ingest.parse import parse_text
from app.services.structurer.rules import RulesStructurer
from app.services.verifier.lint import run as lint_run

router = APIRouter(tags=["lint"])


@router.post("/lint")
def lint_endpoint(body: dict[str, Any]) -> dict[str, Any]:
    doc_type = DocType(body.get("doc_type") or "sop")
    if body.get("blocks"):
        blocks = [Block.model_validate(b) for b in body["blocks"]]
        source = body.get("text") or ""
    else:
        text = body.get("text") or ""
        norm = parse_text(text)
        blocks = RulesStructurer().structure(norm, doc_type)
        source = norm.text
    issues = lint_run(blocks, doc_type, source=source)
    return {"issues": [i.__dict__ for i in issues]}
