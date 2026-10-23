"""LLM provider protocol."""

from __future__ import annotations

from typing import Any, Protocol


class LLMProvider(Protocol):
    name: str

    async def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """Return parsed JSON object from the model."""
        ...

    def available(self) -> bool:
        """True if credentials/base URL allow calls."""
        ...
