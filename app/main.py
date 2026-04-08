"""FastAPI 애플리케이션 진입점."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.database import engine
from app.jobs.scheduler import setup_scheduler, shutdown_scheduler, start_scheduler


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """스케줄러 기동·종료 및 엔진 정리."""
    setup_scheduler()
    start_scheduler()
    yield
    shutdown_scheduler()
    await engine.dispose()


app = FastAPI(
    title="Trend Digest",
    description="AI/테크 트렌드 다이제스트 MVP",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router)
