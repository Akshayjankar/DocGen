"""Run evaluation matrix → results.json + results.md."""

from __future__ import annotations

import json
import time
from pathlib import Path

from metrics import EvalSummary, percentile  # noqa: E402 — sibling module in tests/quality

from app.models.document import DocType, DocumentMeta
from app.services.pipeline import build_document

ROOT = Path(__file__).parent
INPUTS = ROOT / "fixtures" / "inputs"
LOGOS = ROOT / "fixtures" / "logos"


def _ensure_fixtures() -> None:
    INPUTS.mkdir(parents=True, exist_ok=True)
    LOGOS.mkdir(parents=True, exist_ok=True)
    samples = {
        "sop_password.md": """# Purpose
Reset passwords safely for support staff.
## Scope
All support engineers.
## Roles
Support Lead owns this.
## Procedure
1. Verify the requester identity.
2. Open the admin console.
3. Reset the password and notify the user.
## Records
Log the ticket ID.
""",
        "report_quarterly.md": """# Executive Summary
Revenue grew 12% this quarter.
## Findings
Customer churn decreased in enterprise.
## Recommendations
Invest in onboarding automation.
""",
        "setup_install.md": """# Prerequisites
Python 3.12 and Docker.
## Installation
1. Clone the repository.
2. Run make setup.
## Configuration
Copy .env.example to .env.
## Verification
Run make test and confirm green.
""",
    }
    for name, text in samples.items():
        p = INPUTS / name
        if not p.exists():
            p.write_text(text, encoding="utf-8")

    # Generate simple logos if missing
    if not any(LOGOS.glob("*.png")):
        from PIL import Image

        colors = [(30, 90, 180), (20, 120, 80), (180, 60, 40), (90, 40, 140), (40, 40, 40)]
        for i, rgb in enumerate(colors):
            img = Image.new("RGB", (96, 96), rgb)
            img.save(LOGOS / f"logo_{i}.png")


def main(fast: bool = False) -> None:
    _ensure_fixtures()
    inputs = sorted(INPUTS.glob("*.md"))[: 3 if fast else 50]
    logos = sorted(LOGOS.glob("*.png"))[: 2 if fast else 20]
    if not logos:
        logos = [None]  # type: ignore[list-item]

    rows: list[dict] = []
    latencies: list[float] = []
    preserve_ok = 0
    aa_ok = 0
    valid_ok = 0
    total = 0
    failures: list[str] = []

    out_tmp = ROOT / "_tmp_eval"
    out_tmp.mkdir(exist_ok=True)

    for inp in inputs:
        for logo in logos:
            total += 1
            doc_type = DocType.sop
            if "report" in inp.name:
                doc_type = DocType.report
            elif "setup" in inp.name:
                doc_type = DocType.setup_guide
            t0 = time.perf_counter()
            try:
                result = build_document(
                    text_path=inp,
                    logo_path=logo,
                    out_dir=out_tmp / f"{inp.stem}_{logo.stem if logo else 'none'}",
                    doc_type=doc_type,
                    mode="format_only",
                    meta=DocumentMeta(title=inp.stem.replace("_", " ").title()),
                    skip_pdf=True,
                )
                ms = (time.perf_counter() - t0) * 1000
                latencies.append(ms)
                pres = result.content_lock.preserved_pct
                aa = result.theme.contrast.all_aa
                valid = result.validation.ok
                if pres >= 100:
                    preserve_ok += 1
                else:
                    failures.append(f"{inp.name}: preservation {pres}")
                if aa:
                    aa_ok += 1
                else:
                    failures.append(f"{inp.name}/{logo}: AA fail")
                if valid:
                    valid_ok += 1
                else:
                    failures.append(f"{inp.name}: docx invalid {result.validation.errors}")
                rows.append(
                    {
                        "input": inp.name,
                        "logo": logo.name if logo else None,
                        "preserved_pct": pres,
                        "aa": aa,
                        "valid": valid,
                        "latency_ms": round(ms, 1),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{inp.name}: {exc}")

    summary = EvalSummary(
        n=total,
        content_preservation=round(100.0 * preserve_ok / max(total, 1), 2),
        wcag_aa_pass_rate=round(100.0 * aa_ok / max(total, 1), 2),
        docx_validity=round(100.0 * valid_ok / max(total, 1), 2),
        latency_p50_ms=round(percentile(latencies, 50), 1),
        latency_p95_ms=round(percentile(latencies, 95), 1),
        fallback_rate=100.0,  # rules-only eval
        failures=failures,
    )
    payload = {"summary": summary.to_dict(), "rows": rows}
    (ROOT / "results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md = [
        "# Docgen Eval Results",
        "",
        f"- n = {summary.n}",
        f"- Content preservation (format-only) = **{summary.content_preservation}%**",
        f"- WCAG AA pass rate = **{summary.wcag_aa_pass_rate}%**",
        f"- DOCX validity = **{summary.docx_validity}%**",
        f"- Latency p50/p95 = {summary.latency_p50_ms}/{summary.latency_p95_ms} ms",
        "",
    ]
    if failures:
        md.append("## Failures")
        md.extend(f"- {f}" for f in failures[:20])
    (ROOT / "results.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(summary.to_dict(), indent=2))
    if summary.content_preservation < 100 or summary.wcag_aa_pass_rate < 100:
        raise SystemExit(1)


if __name__ == "__main__":
    import sys

    main(fast="--fast" in sys.argv)
