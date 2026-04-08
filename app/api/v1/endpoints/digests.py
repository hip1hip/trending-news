"""다이제스트 조회 API."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.exceptions import not_found
from app.repositories.digest_repository import DigestRepository
from app.schemas.digest import DigestDetail, DigestItemOut, DigestListItem

router = APIRouter(prefix="/digests", tags=["digests"])


@router.get("", response_model=list[DigestListItem])
async def list_digests(
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
) -> list[DigestListItem]:
    """최근 다이제스트 목록."""
    repo = DigestRepository(db)
    rows = await repo.list_recent(limit=min(limit, 100))
    return [DigestListItem.model_validate(r) for r in rows]


@router.get("/{digest_id}", response_model=DigestDetail)
async def get_digest(
    digest_id: int,
    db: AsyncSession = Depends(get_db),
) -> DigestDetail:
    """단건 상세 (순위·원문 링크 포함)."""
    repo = DigestRepository(db)
    d = await repo.get_detail(digest_id)
    if d is None:
        raise not_found("다이제스트를 찾을 수 없습니다.")
    items_out: list[DigestItemOut] = []
    for di in sorted(d.items, key=lambda x: x.rank_order):
        ni = di.normalized_item
        si = ni.source_item
        items_out.append(
            DigestItemOut(
                rank_order=di.rank_order,
                title=si.title,
                url=si.url,
                normalized_title=ni.normalized_title,
                importance_score=ni.importance_score,
            )
        )
    return DigestDetail(
        id=d.id,
        routine_type=d.routine_type,
        run_date=d.run_date,
        summary_text=d.summary_text,
        created_at=d.created_at,
        items=items_out,
    )
