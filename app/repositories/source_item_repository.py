"""source_items 테이블 접근."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source_item import SourceItem


class SourceItemRepository:
    """수집 원시 행 조회·생성."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_url_hash(self, url_hash: str) -> SourceItem | None:
        """url_hash로 기존 행 조회."""
        stmt = select(SourceItem).where(SourceItem.url_hash == url_hash).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        source_type: str,
        source_name: str,
        title: str,
        url: str,
        url_hash: str,
        published_at: datetime | None,
        raw_text: str | None,
        raw_payload: dict[str, Any] | None,
        collected_at: datetime,
    ) -> SourceItem:
        """새 source_item 삽입 (유니크 위반은 상위에서 처리)."""
        row = SourceItem(
            source_type=source_type,
            source_name=source_name,
            title=title,
            url=url,
            url_hash=url_hash,
            published_at=published_at,
            raw_text=raw_text,
            raw_payload=raw_payload,
            collected_at=collected_at,
        )
        self._session.add(row)
        await self._session.flush()
        return row
