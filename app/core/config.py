"""환경 변수 및 애플리케이션 설정 (pydantic-settings)."""

from functools import lru_cache

from pydantic import Field, field_validator
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

    # Upstage Solar — 없으면 목 요약기만 사용
    upstage_api_key: str | None = Field(
        default=None,
        alias="UPSTAGE_API_KEY",
        description="Upstage API 키 (설정 시 solar-pro3 요약)",
    )
    upstage_model: str = Field(
        default="solar-pro3",
        alias="UPSTAGE_MODEL",
        description="채팅 완성 모델명",
    )
    upstage_base_url: str = Field(
        default="https://api.upstage.ai/v1",
        alias="UPSTAGE_BASE_URL",
        description="OpenAI 호환 베이스 URL",
    )

    @field_validator("upstage_api_key", mode="before")
    @classmethod
    def strip_optional_api_key(cls, value: object) -> object:
        """공백·빈 문자열은 미설정으로 처리."""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped if stripped else None
        return value


@lru_cache
def get_settings() -> Settings:
    """설정 싱글톤 (테스트에서 캐시 초기화 가능)."""
    return Settings()
