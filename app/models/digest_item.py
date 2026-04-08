"""다이제스트에 포함된 항목 순위 (digest_items 테이블)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.digest import Digest
    from app.models.normalized_item import NormalizedItem


class DigestItem(Base):
    """digest ↔ normalized_item 연결 및 순서."""

    __tablename__ = "digest_items"
    __table_args__ = (
        UniqueConstraint("digest_id", "rank_order", name="uq_digest_items_digest_rank"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    digest_id: Mapped[int] = mapped_column(
        ForeignKey("digests.id", ondelete="CASCADE"),
        nullable=False,
    )
    normalized_item_id: Mapped[int] = mapped_column(
        ForeignKey("normalized_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)

    digest: Mapped["Digest"] = relationship("Digest", back_populates="items")
    normalized_item: Mapped["NormalizedItem"] = relationship(
        "NormalizedItem",
        back_populates="digest_links",
    )
