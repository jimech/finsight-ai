from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg://finsight:finsight_password@localhost:5432/finsight_db"
    )
    clerk_secret_key: Optional[str] = None
    clerk_jwks_url: Optional[str] = None
    frontend_url: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4.1-mini"
    ai_enabled: bool = False
    embedding_model: str = "text-embedding-3-small"
    embeddings_enabled: bool = False

    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace(
                "postgresql://", "postgresql+psycopg://", 1
            )
        return self.database_url

    @property
    def cors_origins(self) -> list[str]:
        origins = [
            "http://localhost:3000",
            "http://localhost:3001",
        ]
        if self.frontend_url:
            normalized = self.frontend_url.strip().rstrip("/")
            if normalized and normalized not in origins:
                origins.append(normalized)
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
