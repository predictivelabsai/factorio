from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_url: str = Field(default="", alias="DB_URL")
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_secret: str = Field(default="change-me", alias="APP_SECRET")
    port: int = Field(default=5055, alias="PORT")


@lru_cache(maxsize=1)
def settings() -> Settings:
    return Settings()
