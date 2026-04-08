"""digests / digest_items 테이블 접근."""

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.digest import Digest
from app.models.digest_item import DigestItem
from app.models.normalized_item import NormalizedItem


class DigestRepository:
    """다이제스트 저장 및 조회."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_with_items(
        self,
        *,
        routine_type: str,
        run_date: date,
        summary_text: str,
        created_at: datetime,
        ranked_normalized_ids: list[int],
    ) -> Digest:
        """digest + digest_items 트랜잭션 삽입."""
        digest = Digest(
            routine_type=routine_type,
            run_date=run_date,
            summary_text=summary_text,
            created_at=created_at,
        )
        self._session.add(digest)
        await self._session.flush()
        for order, nid in enumerate(ranked_normalized_ids, start=1):
            self._session.add(
                DigestItem(
                    digest_id=digest.id,
                    normalized_item_id=nid,
                    rank_order=order,
                )
            )
        await self._session.flush()
        return digest

    async def list_recent(self, limit: int = 20) -> list[Digest]:
        """최근 다이제스트 목록."""
        stmt = (
            select(Digest)
            .order_by(Digest.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_detail(self, digest_id: int) -> Digest | None:
        """항목·정규화·소스까지 eager 로드."""
        stmt = (
            select(Digest)
            .where(Digest.id == digest_id)
            .options(
                selectinload(Digest.items).selectinload(DigestItem.normalized_item).selectinload(
                    NormalizedItem.source_item
                ),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
