from __future__ import annotations

from app.config import get_settings
from app.services.structurer.providers.openai_compat import OpenAICompatProvider


def make_openai() -> OpenAICompatProvider:
    s = get_settings()
    return OpenAICompatProvider(
        name="openai",
        base_url="https://api.openai.com/v1",
        api_key=s.openai_api_key,
        model="gpt-4o-mini",
    )
