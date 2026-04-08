"""APScheduler: 월·수·금 08:00 (SCHEDULER_TZ, 기본 Asia/Seoul) 다이제스트."""

from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.services.digest_pipeline import run_scheduled_digest_pipeline

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """프로세스 단일 스케줄러 인스턴스."""
    global _scheduler
    if _scheduler is None:
        settings = get_settings()
        _scheduler = AsyncIOScheduler(timezone=ZoneInfo(settings.scheduler_tz))
    return _scheduler


def setup_scheduler() -> None:
    """크론 트리거 등록 (id 고정으로 중복 방지)."""
    sched = get_scheduler()
    settings = get_settings()
    tz = ZoneInfo(settings.scheduler_tz)
    sched.add_job(
        run_scheduled_digest_pipeline,
        CronTrigger(day_of_week="mon,wed,fri", hour=8, minute=0, timezone=tz),
        id="digest_tech_trend",
        kwargs={"routine_type": "tech_trend"},
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )


def start_scheduler() -> None:
    """이벤트 루프가 실행 중일 때 호출."""
    get_scheduler().start()


def shutdown_scheduler() -> None:
    """앱 종료 시 대기 종료."""
    if _scheduler is not None:
        _scheduler.shutdown(wait=True)
