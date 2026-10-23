from __future__ import annotations

from app.config import get_settings
from app.services.structurer.providers.openai_compat import OpenAICompatProvider


def make_openrouter() -> OpenAICompatProvider:
    s = get_settings()
    return OpenAICompatProvider(
        name="openrouter",
        base_url="https://openrouter.ai/api/v1",
        api_key=s.openrouter_api_key,
        model=s.openrouter_model,
        extra_headers={"HTTP-Referer": "https://docgen.local", "X-Title": "Docgen"},
    )
