"""다이제스트 API 스키마."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class DigestListItem(BaseModel):
    """목록용 다이제스트 요약."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    routine_type: str
    run_date: date
    created_at: datetime


class DigestItemOut(BaseModel):
    """다이제스트에 포함된 항목."""

    model_config = ConfigDict(from_attributes=True)

    rank_order: int
    title: str = Field(..., description="원본 제목 (source_item)")
    url: str
    normalized_title: str
    importance_score: float


class DigestDetail(BaseModel):
    """단건 상세."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    routine_type: str
    run_date: date
    summary_text: str
    created_at: datetime
    items: list[DigestItemOut]
