"""Shared OpenAI-compatible chat completions (Groq, OpenRouter, Ollama, OpenAI)."""

from __future__ import annotations

import json
from typing import Any

import httpx


class OpenAICompatProvider:
    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        api_key: str,
        model: str,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.extra_headers = extra_headers or {}

    def available(self) -> bool:
        if self.name == "ollama":
            return bool(self.base_url)
        return bool(self.api_key)

    async def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        headers = {"Content-Type": "application/json", **self.extra_headers}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        body: dict[str, Any] = {
            "model": self.model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=body,
            )
            if resp.status_code >= 400:
                raise RuntimeError(f"{self.name} HTTP {resp.status_code}: {resp.text[:300]}")
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
