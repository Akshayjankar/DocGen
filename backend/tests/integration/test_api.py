"""API integration tests (rules-only, no LLM)."""

from __future__ import annotations

import io
import time

from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app


def _logo() -> bytes:
    img = Image.new("RGB", (64, 64), (30, 90, 180))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


SOP = """# Purpose

Reset passwords safely.

## Procedure

1. Verify identity.
2. Open admin console.
3. Reset and notify.
"""


def test_health() -> None:
    client = TestClient(create_app())
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_theme_extract() -> None:
    client = TestClient(create_app())
    r = client.post(
        "/api/v1/themes/extract",
        files={"logo": ("logo.png", _logo(), "image/png")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["contrast"]["all_aa"] is True
    assert body["palette"]["primary"].startswith("#")


def test_document_job_rules() -> None:
    client = TestClient(create_app())
    r = client.post(
        "/api/v1/documents",
        data={
            "text": SOP,
            "doc_type": "sop",
            "mode": "format_only",
            "force_rules": "true",
            "meta": '{"title":"API SOP","version":"1.0","author":"Test"}',
        },
        files={"logo": ("logo.png", _logo(), "image/png")},
    )
    assert r.status_code == 200
    job_id = r.json()["job_id"]

    # Poll until done
    status = None
    for _ in range(50):
        jr = client.get(f"/api/v1/jobs/{job_id}")
        status = jr.json()["status"]
        if status in ("done", "failed"):
            break
        time.sleep(0.1)
    assert status == "done", jr.json()
    assert jr.json()["preserved_pct"] == 100.0

    dl = client.get(f"/api/v1/documents/{job_id}/download?format=docx")
    assert dl.status_code == 200
    assert len(dl.content) > 1000

    blocks = client.get(f"/api/v1/documents/{job_id}/blocks")
    assert blocks.status_code == 200
    assert len(blocks.json()["blocks"]) >= 1


def test_brand_kits_crud() -> None:
    client = TestClient(create_app())
    r = client.post("/api/v1/brand-kits", json={"name": "Acme", "theme": {"name": "x"}})
    assert r.status_code == 200
    kit_id = r.json()["id"]
    assert client.get(f"/api/v1/brand-kits/{kit_id}").status_code == 200
    assert client.delete(f"/api/v1/brand-kits/{kit_id}").status_code == 200


def test_lint() -> None:
    client = TestClient(create_app())
    r = client.post("/api/v1/lint", json={"text": SOP, "doc_type": "sop"})
    assert r.status_code == 200
    assert "issues" in r.json()
