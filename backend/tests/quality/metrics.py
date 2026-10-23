"""Eval metrics helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class EvalSummary:
    n: int = 0
    content_preservation: float = 100.0
    wcag_aa_pass_rate: float = 100.0
    docx_validity: float = 100.0
    structure_f1: float | None = None
    latency_p50_ms: float | None = None
    latency_p95_ms: float | None = None
    fallback_rate: float = 0.0
    cost_per_doc: float = 0.0
    failures: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = int(round((p / 100) * (len(s) - 1)))
    return s[k]
