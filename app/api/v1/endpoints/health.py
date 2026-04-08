"""헬스 체크."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """DB 연결 여부를 포함한 간단 헬스."""
    database = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        database = "error"
    overall = "ok" if database == "ok" else "degraded"
    return HealthResponse(status=overall, database=database)
