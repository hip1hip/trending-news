"""작업 트리거 요청/응답."""

from pydantic import BaseModel, Field


class RunDigestRequest(BaseModel):
    """수동 다이제스트 실행 옵션."""

    routine_type: str = Field(
        default="tech_trend",
        description="global_ai | tech_trend | community_trend",
    )


class RunDigestResponse(BaseModel):
    """비동기 작업 접수 결과."""

    accepted: bool = Field(True, description="백그라운드 실행 수락 여부")
    job_run_id: int = Field(..., description="job_runs PK")
    message: str = Field(default="파이프라인이 백그라운드에서 시작되었습니다.")
