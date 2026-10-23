"""Application settings (pydantic-settings)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app import APP_NAME


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = APP_NAME
    env: str = "development"
    frontend_origin: str = "http://localhost:3000"
    next_public_api_url: str = "http://localhost:8000"
    database_url: str = "sqlite:///./docgen.db"

    llm_provider_order: str = "gemini,groq,openrouter,ollama"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    openrouter_api_key: str = ""
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_cache: bool = True
    gemini_rpm: int = 10
    gemini_rpd: int = 200
    groq_rpm: int = 20
    groq_rpd: int = 500

    max_upload_mb: int = 10
    file_ttl_minutes: int = 60
    store_history: bool = False
    rate_limit_per_min: int = 20
    soffice_path: str = "/usr/bin/soffice"
    # native = PyMuPDF from blocks/theme (default, no LibreOffice)
    # libreoffice = convert DOCX via soffice
    # auto = native when blocks available, else LibreOffice
    pdf_engine: str = "native"
    pdf_timeout_sec: int = 60
    watermark_free_tier: bool = True

    data_dir: Path = Path("./data")

    @property
    def llm_providers(self) -> list[str]:
        return [p.strip() for p in self.llm_provider_order.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
