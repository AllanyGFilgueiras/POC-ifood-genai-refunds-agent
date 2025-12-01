from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel, Field, AliasChoices
from pydantic_settings import SettingsConfigDict


class Settings(BaseModel):
    app_name: str = "ifood-genai-refunds-agent"
    csv_path: Path = Field(default=Path("data/base_conhecimento_ifood_genai-exemplo.csv"))
    vector_store_path: Path = Field(default=Path("data/vector_store"))
    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AGENT_OPENAI_API_KEY", "OPENAI_API_KEY"),
    )
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"
    retrieval_k: int = 4
    similarity_threshold: float = 0.6
    use_fake_embeddings: bool = False

    model_config = SettingsConfigDict(env_prefix="AGENT_", env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
