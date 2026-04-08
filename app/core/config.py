"""환경 변수 및 애플리케이션 설정 (pydantic-settings)."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """런타임 설정. 필수 값 누락 시 기동 실패(fail-fast)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        ...,
        alias="DATABASE_URL",
        description="SQLAlchemy async URL (postgresql+asyncpg://...)",
    )
    discord_webhook_url: str = Field(
        ...,
        alias="DISCORD_WEBHOOK_URL",
        description="Discord Incoming Webhook URL",
    )
    scheduler_tz: str = Field(
        default="Asia/Seoul",
        alias="SCHEDULER_TZ",
        description="APScheduler 크론 타임존",
    )


@lru_cache
def get_settings() -> Settings:
    """설정 싱글톤 (테스트에서 캐시 초기화 가능)."""
    return Settings()
