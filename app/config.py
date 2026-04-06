from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="openai/gpt-4.1-mini", alias="OPENROUTER_MODEL")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENROUTER_BASE_URL",
    )
    openrouter_http_referer: str = Field(default="http://localhost:8000", alias="OPENROUTER_HTTP_REFERER")
    openrouter_title: str = Field(default="SmartWiki2", alias="OPENROUTER_TITLE")

    wiki_vault_path: str = Field(default="", alias="WIKI_VAULT_PATH")
    wiki_vault_git_url: str = Field(default="", alias="WIKI_VAULT_GIT_URL")

    smartwiki_env: str = Field(default="dev", alias="SMARTWIKI_ENV")
    # Relative to process cwd (repo root for Makefile/scripts and Docker WORKDIR /app).
    smartwiki_site_dir: str = Field(default="./site", alias="SMARTWIKI_SITE_DIR")
    smartwiki_quartz_dir: str = Field(default="publisher/quartz", alias="SMARTWIKI_QUARTZ_DIR")
    smartwiki_log_level: str = Field(default="INFO", alias="SMARTWIKI_LOG_LEVEL")

    @property
    def running_in_container(self) -> bool:
        return Path("/.dockerenv").exists()

    @property
    def resolved_vault_path(self) -> Path:
        if self.wiki_vault_path:
            return Path(self.wiki_vault_path).resolve()
        if self.running_in_container:
            return Path("/app/wiki_vault")
        return Path("./wiki_vault").resolve()

    @property
    def resolved_site_dir(self) -> Path:
        return Path(self.smartwiki_site_dir).resolve()

    @property
    def resolved_quartz_dir(self) -> Path:
        return Path(self.smartwiki_quartz_dir).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
