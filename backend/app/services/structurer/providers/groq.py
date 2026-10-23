from __future__ import annotations

from app.config import get_settings
from app.services.structurer.providers.openai_compat import OpenAICompatProvider


def make_groq() -> OpenAICompatProvider:
    s = get_settings()
    return OpenAICompatProvider(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        api_key=s.groq_api_key,
        model=s.groq_model,
    )
