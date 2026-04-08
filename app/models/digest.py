"""다이제스트 본문 (digests 테이블)."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.digest_item import DigestItem


class Digest(Base):
    """한 번의 루틴 실행에 대한 요약 결과."""

    __tablename__ = "digests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    routine_type: Mapped[str] = mapped_column(String(64), nullable=False)
    run_date: Mapped[date] = mapped_column(Date, nullable=False)
    summary_text: Mapped[str] = mapped_column(Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    items: Mapped[list["DigestItem"]] = relationship(
        "DigestItem",
        back_populates="digest",
        cascade="all, delete-orphan",
        order_by="DigestItem.rank_order",
    )
