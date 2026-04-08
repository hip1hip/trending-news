"""작업 트리거 API."""

from fastapi import APIRouter, HTTPException, status

from app.schemas.job import RunDigestRequest, RunDigestResponse
from app.services.digest_pipeline import (
    ALLOWED_ROUTINES,
    PipelineBusyError,
    start_manual_digest_background,
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

    이미 다른 파이프라인이 돌고 있으면 429 를 반환합니다(이중 알림 방지).
    """
    if body.routine_type not in ALLOWED_ROUTINES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"routine_type 은 {sorted(ALLOWED_ROUTINES)} 중 하나여야 합니다.",
        )
    try:
        job_run_id = await start_manual_digest_background(body.routine_type)
    except PipelineBusyError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="이미 다이제스트 파이프라인이 실행 중입니다. 잠시 후 다시 시도하세요.",
        ) from None
    return RunDigestResponse(job_run_id=job_run_id)
