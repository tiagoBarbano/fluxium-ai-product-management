from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FLUXIUM_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "Fluxium AI Product Management API"
    environment: str = Field(default="local", min_length=1)
    api_prefix: str = "/api/v1"
    cors_allowed_origins: str = "http://localhost:3000"
    mongo_uri: str = "mongodb://localhost:27017/?replicaSet=rs0"
    mongo_database: str = "fluxium"
    redis_url: str = "redis://:redis1234@localhost:6379/0"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = ""
    default_workspace_id: str = ""
    identity_jwt_secret: str = ""
    identity_jwt_algorithm: str = "HS256"
    identity_jwt_private_key: str = ""
    identity_jwt_public_key: str = ""
    identity_jwt_key_id: str = "fluxium-internal"
    identity_jwt_issuer: str = ""
    identity_jwt_audience: str = ""
    identity_access_token_ttl_seconds: int = Field(default=7200, ge=60)
    identity_refresh_token_ttl_seconds: int = Field(default=0, ge=0)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
