"""Optional Anthropic provider (paid)."""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import get_settings


class AnthropicProvider:
    name = "anthropic"

    def __init__(self) -> None:
        s = get_settings()
        self.api_key = s.anthropic_api_key
        self.model = "claude-3-5-haiku-latest"

    def available(self) -> bool:
        return bool(self.api_key)

    async def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body = {
            "model": self.model,
            "max_tokens": 4096,
            "temperature": temperature,
            "system": system + "\nRespond with JSON only.",
            "messages": [{"role": "user", "content": user}],
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages", headers=headers, json=body
            )
            if resp.status_code >= 400:
                raise RuntimeError(f"anthropic HTTP {resp.status_code}: {resp.text[:300]}")
            data = resp.json()
            text = data["content"][0]["text"]
            return json.loads(text)
