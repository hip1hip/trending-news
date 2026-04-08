"""normalized_items 테이블 접근."""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.normalized_item import NormalizedItem


class NormalizedItemRepository:
    """정규화 행 생성."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        source_item_id: int,
        normalized_title: str,
        normalized_text: str | None,
        tags: dict | list | None,
        importance_score: float,
        duplicate_group_key: str,
        created_at: datetime,
    ) -> NormalizedItem:
        """정규화 행 삽입."""
        row = NormalizedItem(
            source_item_id=source_item_id,
            normalized_title=normalized_title,
            normalized_text=normalized_text,
            tags=tags,
            importance_score=importance_score,
            duplicate_group_key=duplicate_group_key,
            created_at=created_at,
        )
        self._session.add(row)
        await self._session.flush()
        return row
