"""수집→정규화→랭킹→요약→저장→Discord 파이프라인."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.base import RawCollectedItem
from app.collectors.github_trending import collect_github_trending_mock
from app.collectors.hacker_news import collect_hacker_news
from app.core.config import Settings, get_settings
from app.core.database import AsyncSessionLocal
from app.delivery.discord_webhook import build_discord_webhook_payload, send_discord_webhook
from app.models.job_run import JobRun
from app.normalization import compute_duplicate_group_key, hash_url, normalize_title
from app.ranking import total_importance_score
from app.repositories.digest_repository import DigestRepository
from app.repositories.job_run_repository import JobRunRepository
from app.repositories.normalized_item_repository import NormalizedItemRepository
from app.repositories.source_item_repository import SourceItemRepository
from app.summarization.mock_summarizer import summarize_digest_mock
from app.summarization.upstage_summarizer import summarize_with_upstage

ALLOWED_ROUTINES = frozenset({"global_ai", "tech_trend", "community_trend"})

# 수동 트리거와 스케줄이 동시에 돌지 않도록 세마포어 1
_pipeline_sem = asyncio.Semaphore(1)
MANUAL_LOCK_WAIT_SEC = 0.08


class PipelineBusyError(Exception):
    """이미 다른 다이제스트 파이프라인이 실행 중일 때."""


def _coerce_published_at(value: datetime | str | None) -> datetime | None:
    """수집 dict의 published_at을 datetime으로 통일."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        s = value.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            return None
    return None


async def begin_digest_job() -> int:
    """
    job_runs 를 running 으로 한 번 커밋하고 PK만 반환.

    API는 이 값을 즉시 응답에 실을 수 있습니다.
    """
    now = datetime.now(tz=UTC)
    async with AsyncSessionLocal() as session:
        job_repo = JobRunRepository(session)
        job = await job_repo.start("digest_pipeline", now)
        await session.commit()
        return job.id


async def start_manual_digest_background(routine_type: str) -> int:
    """
    수동 실행: 슬롯이 없으면 PipelineBusyError.

    job_run_id 는 즉시 반환하고 본 처리는 백그라운드 태스크에서 진행합니다.
    """
    if routine_type not in ALLOWED_ROUTINES:
        raise ValueError(f"지원하지 않는 routine_type: {routine_type}")
    try:
        await asyncio.wait_for(_pipeline_sem.acquire(), timeout=MANUAL_LOCK_WAIT_SEC)
    except asyncio.TimeoutError as e:
        raise PipelineBusyError from e
    try:
        jid = await begin_digest_job()
    except Exception:
        _pipeline_sem.release()
        raise

    async def _task() -> None:
        try:
            await continue_digest_pipeline(jid, routine_type)
        finally:
            _pipeline_sem.release()

    asyncio.create_task(_task())
    return jid


async def run_scheduled_digest_pipeline(routine_type: str = "tech_trend") -> None:
    """스케줄러용: 동시 실행 1개(수동과도 공유)."""
    async with _pipeline_sem:
        jid = await begin_digest_job()
        await continue_digest_pipeline(jid, routine_type=routine_type)


async def continue_digest_pipeline(job_id: int, routine_type: str = "tech_trend") -> None:
    """
    실제 수집·DB·Discord 까지 수행. `begin_digest_job` 직후 같은 job_id 로 호출합니다.
    """
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        await _run_digest_transaction(session, settings, job_id=job_id, routine_type=routine_type)


async def _run_digest_transaction(
    session: AsyncSession,
    settings: Settings,
    *,
    job_id: int,
    routine_type: str,
) -> None:
    if routine_type not in ALLOWED_ROUTINES:
        raise ValueError(f"지원하지 않는 routine_type: {routine_type}")

    now = datetime.now(tz=UTC)
    tz = ZoneInfo(settings.scheduler_tz)
    run_date = now.astimezone(tz).date()
    run_label = now.astimezone(tz).strftime("%Y-%m-%d %H:%M %Z")

    job_repo = JobRunRepository(session)
    source_repo = SourceItemRepository(session)
    norm_repo = NormalizedItemRepository(session)
    digest_repo = DigestRepository(session)

    top: list[tuple[Any, str, str, str]] = []
    summary_payload: dict[str, Any] = {"summary": "", "items": []}

    async with httpx.AsyncClient() as client:
        try:
            hn_items = await collect_hacker_news(client)
            gh_items = collect_github_trending_mock()
            collected: list[RawCollectedItem] = [*hn_items, *gh_items]

            # (ni, title, url, snippet)
            run_rows: list[tuple[Any, str, str, str]] = []

            for raw in collected:
                url = raw["url"].strip()
                title = (raw.get("title") or "").strip() or "(no title)"
                url_h = hash_url(url)
                published_at = _coerce_published_at(raw.get("published_at"))
                raw_text = raw.get("raw_text") or ""
                raw_payload = raw.get("raw_payload")

                source_row = await source_repo.get_by_url_hash(url_h)
                if source_row is None:
                    try:
                        source_row = await source_repo.create(
                            source_type=raw.get("source") or "unknown",
                            source_name=raw.get("source_name")
                            or raw.get("source")
                            or "unknown",
                            title=title,
                            url=url,
                            url_hash=url_h,
                            published_at=published_at,
                            raw_text=raw_text or None,
                            raw_payload=dict(raw_payload) if raw_payload else None,
                            collected_at=now,
                        )
                    except IntegrityError:
                        await session.rollback()
                        source_row = await source_repo.get_by_url_hash(url_h)
                        if source_row is None:
                            raise

                body_for_snip = source_row.raw_text or raw_text or ""
                snippet = (body_for_snip)[:2500]

                nt = normalize_title(title)
                dgk = compute_duplicate_group_key(title)
                payload_for_score: dict[str, Any] | None
                if source_row.raw_payload is not None:
                    payload_for_score = dict(source_row.raw_payload)
                elif raw_payload is not None:
                    payload_for_score = dict(raw_payload)
                else:
                    payload_for_score = None
                score = total_importance_score(
                    published_at=source_row.published_at or published_at,
                    title=title,
                    raw_text=raw_text,
                    raw_payload=payload_for_score,
                    now=now,
                )

                ni = await norm_repo.create(
                    source_item_id=source_row.id,
                    normalized_title=nt,
                    normalized_text=raw_text or None,
                    tags={"source": raw.get("source")},
                    importance_score=score,
                    duplicate_group_key=dgk,
                    created_at=now,
                )
                run_rows.append((ni, title, url, snippet))

            best_by_key: dict[str, tuple[Any, str, str, str]] = {}
            for ni, t, u, sn in run_rows:
                cur = best_by_key.get(ni.duplicate_group_key)
                if cur is None or ni.importance_score > cur[0].importance_score:
                    best_by_key[ni.duplicate_group_key] = (ni, t, u, sn)

            ranked = sorted(
                best_by_key.values(),
                key=lambda x: x[0].importance_score,
                reverse=True,
            )
            top = ranked[:5]

            ranked_for_summary = [
                (title, url, snip, ni.importance_score) for ni, title, url, snip in top
            ]
            if settings.upstage_api_key:
                summary_payload = await summarize_with_upstage(
                    client,
                    api_key=settings.upstage_api_key,
                    model=settings.upstage_model,
                    base_url=settings.upstage_base_url,
                    ranked=ranked_for_summary,
                )
            else:
                summary_payload = summarize_digest_mock(
                    [(t, u, sc) for t, u, _, sc in ranked_for_summary],
                )

            ranked_ids = [ni.id for ni, _, _, _ in top]
            await digest_repo.create_with_items(
                routine_type=routine_type,
                run_date=run_date,
                summary_text=summary_payload["summary"],
                created_at=now,
                ranked_normalized_ids=ranked_ids,
            )

            job_loaded = await session.get(JobRun, job_id)
            if job_loaded is not None:
                await job_repo.finish_success(job_loaded, datetime.now(tz=UTC))
            await session.commit()

        except Exception as exc:
            await session.rollback()
            async with session.begin():
                job_loaded = await session.get(JobRun, job_id)
                if job_loaded is not None:
                    await job_repo.finish_failure(
                        job_loaded,
                        datetime.now(tz=UTC),
                        str(exc),
                    )
            raise

        discord_payload = build_discord_webhook_payload(
            summary_payload=summary_payload,
            routine_type=routine_type,
            run_label=run_label,
        )
        await send_discord_webhook(client, settings.discord_webhook_url, discord_payload)
