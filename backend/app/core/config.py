from functools import lru_cache

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class PublicRuntimeConfig(BaseModel):
    app_env: str
    app_version: str
    supabase_enabled: bool


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "best-select backend"
    app_version: str = "0.1.0"
    app_env: str = "dev"

    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_table_snapshots: str = "market_snapshots"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
