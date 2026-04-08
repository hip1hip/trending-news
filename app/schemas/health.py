"""헬스 체크 응답."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """서비스 및 DB 가용 상태."""

    status: str = Field(..., description="전체 상태: ok / degraded")
    database: str = Field(..., description="DB 연결: ok / error")
