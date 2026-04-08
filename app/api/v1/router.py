"""v1 API 라우터 묶음."""

from fastapi import APIRouter

from app.api.v1.endpoints import digests, health, jobs

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(jobs.router)
api_router.include_router(digests.router)
