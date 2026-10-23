"""Regex (+ optional Presidio) PII redaction with reversible mapping."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE = re.compile(
    r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)\d{3,4}[\s.-]?\d{3,4}\b"
)
_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_ID_LIKE = re.compile(r"\b(?:SSN|Aadhaar|PAN)[:\s-]*[A-Z0-9-]{4,}\b", re.I)


@dataclass
class PiiMapping:
    """Server-side only; never persist."""

    tokens: dict[str, str] = field(default_factory=dict)  # token → original


def redact(text: str) -> tuple[str, PiiMapping]:
    mapping = PiiMapping()
    counter = 0

    def _sub(match: re.Match[str], kind: str) -> str:
        nonlocal counter
        counter += 1
        token = f"[{kind}_{counter}]"
        mapping.tokens[token] = match.group(0)
        return token

    out = text
    out = _EMAIL.sub(lambda m: _sub(m, "EMAIL"), out)
    out = _PHONE.sub(lambda m: _sub(m, "PHONE"), out)
    out = _IPV4.sub(lambda m: _sub(m, "IP"), out)
    out = _ID_LIKE.sub(lambda m: _sub(m, "ID"), out)

    # Optional Presidio when extra installed.
    try:
        from presidio_analyzer import AnalyzerEngine  # type: ignore

        analyzer = AnalyzerEngine()
        results = analyzer.analyze(text=out, language="en")
        # Replace from end so offsets stay valid.
        for r in sorted(results, key=lambda x: x.start, reverse=True):
            original = out[r.start : r.end]
            counter += 1
            token = f"[{r.entity_type}_{counter}]"
            mapping.tokens[token] = original
            out = out[: r.start] + token + out[r.end :]
    except Exception:
        pass

    return out, mapping


def restore(text: str, mapping: PiiMapping) -> str:
    out = text
    # Longer tokens first to avoid partial collisions.
    for token, original in sorted(mapping.tokens.items(), key=lambda kv: -len(kv[0])):
        out = out.replace(token, original)
    return out
