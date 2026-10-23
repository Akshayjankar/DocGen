from __future__ import annotations

from app.config import get_settings
from app.services.structurer.providers.openai_compat import OpenAICompatProvider


def make_ollama() -> OpenAICompatProvider:
    s = get_settings()
    return OpenAICompatProvider(
        name="ollama",
        base_url=f"{s.ollama_base_url.rstrip('/')}/v1",
        api_key="ollama",
        model=s.ollama_model,
    )
