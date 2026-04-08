"""FastAPI 의존성 주입."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """API 라우터용 DB 세션."""
    async for session in get_async_session():
        yield session
