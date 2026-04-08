"""정규화·점수화된 항목 (normalized_items 테이블)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.digest_item import DigestItem
    from app.models.source_item import SourceItem


class NormalizedItem(Base):
    """source_items 기준 정규화 및 중복 그룹 정보."""

    __tablename__ = "normalized_items"
    __table_args__ = (Index("ix_normalized_items_duplicate_group", "duplicate_group_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_item_id: Mapped[int] = mapped_column(
        ForeignKey("source_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    normalized_title: Mapped[str] = mapped_column(String(512), nullable=False)
    normalized_text: Mapped[str | None] = mapped_column(Text())
    tags: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONB)
    importance_score: Mapped[float] = mapped_column(nullable=False, default=0.0)
    duplicate_group_key: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    source_item: Mapped["SourceItem"] = relationship(
        "SourceItem",
        back_populates="normalized_items",
    )
    digest_links: Mapped[list["DigestItem"]] = relationship(
        "DigestItem",
        back_populates="normalized_item",
    )
