"""원천 수집 항목 (source_items 테이블)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.normalized_item import NormalizedItem


class SourceItem(Base):
    """외부 소스에서 수집한 원시 레코드."""

    __tablename__ = "source_items"
    __table_args__ = (
        UniqueConstraint("url", name="uq_source_items_url"),
        UniqueConstraint("url_hash", name="uq_source_items_url_hash"),
        Index("ix_source_items_url_hash", "url_hash"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_text: Mapped[str | None] = mapped_column(Text())
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    normalized_items: Mapped[list[NormalizedItem]] = relationship(
        "NormalizedItem",
        back_populates="source_item",
        cascade="all, delete-orphan",
    )
