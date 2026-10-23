"""Provider router with order, basic rate awareness, and fallback."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.services.structurer.providers.anthropic import AnthropicProvider
from app.services.structurer.providers.gemini import GeminiProvider
from app.services.structurer.providers.groq import make_groq
from app.services.structurer.providers.ollama import make_ollama
from app.services.structurer.providers.openai import make_openai
from app.services.structurer.providers.openrouter import make_openrouter

_CACHE: dict[str, dict[str, Any]] = {}
_HITS: dict[str, list[float]] = {}


def _providers() -> list[Any]:
    return [
        GeminiProvider(),
        make_groq(),
        make_openrouter(),
        make_ollama(),
        AnthropicProvider(),
        make_openai(),
    ]


def _ordered() -> list[Any]:
    settings = get_settings()
    order = settings.llm_providers
    by_name = {p.name: p for p in _providers()}
    out: list[Any] = []
    for name in order:
        if name in by_name:
            out.append(by_name[name])
    # append any extras not listed
    for p in _providers():
        if p not in out:
            out.append(p)
    return out


def _under_limit(name: str) -> bool:
    settings = get_settings()
    rpm = {"gemini": settings.gemini_rpm, "groq": settings.groq_rpm}.get(name, 60)
    now = time.time()
    window = _HITS.setdefault(name, [])
    _HITS[name] = [t for t in window if now - t < 60]
    return len(_HITS[name]) < rpm


def _record_hit(name: str) -> None:
    _HITS.setdefault(name, []).append(time.time())


class ProviderRouter:
    def __init__(self) -> None:
        self.last_provider: str | None = None
        self.last_error: str | None = None

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(min=0.5, max=4), reraise=True)
    async def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: dict[str, Any] | None = None,
        temperature: float = 0.0,
        cache_key: str | None = None,
    ) -> dict[str, Any]:
        settings = get_settings()
        if settings.llm_cache and cache_key and cache_key in _CACHE:
            return _CACHE[cache_key]

        errors: list[str] = []
        for provider in _ordered():
            if not provider.available():
                continue
            if not _under_limit(provider.name):
                errors.append(f"{provider.name}: rate limited locally")
                continue
            try:
                result = await provider.complete_json(
                    system=system, user=user, schema=schema, temperature=temperature
                )
                _record_hit(provider.name)
                self.last_provider = provider.name
                if settings.llm_cache and cache_key:
                    _CACHE[cache_key] = result
                return result
            except Exception as exc:  # noqa: BLE001
                msg = f"{provider.name}: {exc}"
                errors.append(msg)
                self.last_error = msg
                continue
        raise RuntimeError("All LLM providers failed: " + "; ".join(errors) if errors else "none available")


def cache_key_for(text: str, doc_type: str, mode: str) -> str:
    h = hashlib.sha256(f"{mode}:{doc_type}:{text}".encode()).hexdigest()
    return h


def provider_status() -> list[dict[str, Any]]:
    return [
        {"name": p.name, "available": p.available()}
        for p in _ordered()
    ]
