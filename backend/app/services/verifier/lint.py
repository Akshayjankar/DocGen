"""Document linting against doc-type templates."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from app.models.blocks import Block
from app.models.document import DocType

_VERB = re.compile(
    r"\b(click|open|run|set|create|update|delete|verify|ensure|check|install|"
    r"configure|enter|select|review|submit|copy|paste|add|remove|start|stop|"
    r"enable|disable|navigate|confirm|document|record|notify|monitor|triage|"
    r"isolate|escalate|respond|revoke|contain|detect|recover|log)\b",
    re.I,
)


@dataclass
class LintIssue:
    code: str
    severity: str  # error | warning | info
    message: str
    block_id: str | None = None


def _templates_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "templates" / "doc_types"


def load_template(doc_type: DocType) -> dict[str, Any]:
    path = _templates_dir() / f"{doc_type.value}.yaml"
    if not path.exists():
        return {"required_sections": [], "name": doc_type.value}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def run(blocks: list[Block], doc_type: DocType, source: str = "") -> list[LintIssue]:
    issues: list[LintIssue] = []
    tmpl = load_template(doc_type)
    required: list[str] = list(tmpl.get("required_sections") or [])

    headings = [
        (b, b.resolved_text(source) if source else (b.text or ""))
        for b in blocks
        if b.type == "heading"
    ]
    heading_texts = [h.lower() for _, h in headings]

    for section in required:
        if not any(section.lower() in h for h in heading_texts):
            issues.append(
                LintIssue(
                    code="missing_section",
                    severity="warning",
                    message=f"Missing recommended section: {section}",
                )
            )

    # Duplicate headings
    seen: dict[str, str] = {}
    for b, text in headings:
        key = text.strip().lower()
        if key in seen:
            issues.append(
                LintIssue(
                    code="duplicate_heading",
                    severity="warning",
                    message=f"Duplicate heading: {text}",
                    block_id=b.id,
                )
            )
        seen[key] = b.id

    # Steps without verbs
    for b in blocks:
        if b.type != "steps":
            continue
        items = b.resolved_items(source) if source else [str(i) for i in (b.items or [])]
        for item in items:
            if item and not _VERB.search(item):
                issues.append(
                    LintIssue(
                        code="vague_step",
                        severity="info",
                        message=f"Step may lack an action verb: {item[:80]}",
                        block_id=b.id,
                    )
                )

    # Orphan headings (heading with no following content before next heading)
    for i, b in enumerate(blocks):
        if b.type != "heading":
            continue
        if i + 1 >= len(blocks) or blocks[i + 1].type == "heading":
            issues.append(
                LintIssue(
                    code="orphan_heading",
                    severity="info",
                    message=f"Heading has no content beneath it: {b.resolved_text(source) if source else b.text}",
                    block_id=b.id,
                )
            )

    # Very long paragraphs
    for b in blocks:
        if b.type != "paragraph":
            continue
        text = b.resolved_text(source) if source else (b.text or "")
        if len(text) > 800:
            issues.append(
                LintIssue(
                    code="long_paragraph",
                    severity="info",
                    message=f"Paragraph is very long ({len(text)} chars)",
                    block_id=b.id,
                )
            )

    # Inconsistent term casing (simple heuristic on repeated title-case words)
    terms: dict[str, set[str]] = {}
    for b in blocks:
        text = b.resolved_text(source) if source else (b.text or "")
        for word in re.findall(r"\b[A-Z][a-zA-Z]{2,}\b", text):
            terms.setdefault(word.lower(), set()).add(word)
    for lower, variants in terms.items():
        if len(variants) > 1:
            issues.append(
                LintIssue(
                    code="inconsistent_casing",
                    severity="info",
                    message=f"Inconsistent casing for '{lower}': {', '.join(sorted(variants))}",
                )
            )

    return issues
