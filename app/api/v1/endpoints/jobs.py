"""작업 트리거 API."""

import asyncio

from fastapi import APIRouter, HTTPException, status

from app.schemas.job import RunDigestRequest, RunDigestResponse
from app.services.digest_pipeline import (
    ALLOWED_ROUTINES,
    begin_digest_job,
    continue_digest_pipeline,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post(
    "/run-digest",
    response_model=RunDigestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def run_digest(body: RunDigestRequest) -> RunDigestResponse:
    """
    다이제스트 파이프라인을 백그라운드에서 실행합니다.

    즉시 `job_run_id` 를 반환하며, 실제 처리는 동일 이벤트 루프에서 태스크로 진행됩니다.
    """
    if body.routine_type not in ALLOWED_ROUTINES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"routine_type 은 {sorted(ALLOWED_ROUTINES)} 중 하나여야 합니다.",
        )
    job_run_id = await begin_digest_job()
    asyncio.create_task(continue_digest_pipeline(job_run_id, body.routine_type))
    return RunDigestResponse(job_run_id=job_run_id)
