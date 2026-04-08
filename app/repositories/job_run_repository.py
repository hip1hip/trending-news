"""job_runs 테이블 접근."""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_run import JobRun


class JobRunRepository:
    """작업 실행 로그."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def start(self, job_name: str, started_at: datetime) -> JobRun:
        """status=running 으로 시작 행 생성."""
        row = JobRun(
            job_name=job_name,
            status="running",
            started_at=started_at,
            finished_at=None,
            error_message=None,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def finish_success(self, row: JobRun, finished_at: datetime) -> None:
        """성공 종료."""
        row.status = "success"
        row.finished_at = finished_at
        row.error_message = None

    async def finish_failure(
        self,
        row: JobRun,
        finished_at: datetime,
        error_message: str,
    ) -> None:
        """실패 종료."""
        row.status = "failed"
        row.finished_at = finished_at
        row.error_message = error_message[:4000]
