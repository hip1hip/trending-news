"""Hacker News Firebase API 비동기 수집."""

import asyncio
from datetime import UTC, datetime
from typing import Any

import httpx

from app.collectors.base import RawCollectedItem

HN_BASE = "https://hacker-news.firebaseio.com/v0"


def _parse_hn_time(ts: int | None) -> datetime | None:
    """HN `time` 필드(초) → UTC datetime."""
    if ts is None:
        return None
    return datetime.fromtimestamp(int(ts), tz=UTC)


async def collect_hacker_news(
    client: httpx.AsyncClient,
    *,
    top_n: int = 30,
    max_concurrent: int = 10,
) -> list[RawCollectedItem]:
    """
    상위 스토리 ID를 가져온 뒤 아이템을 병렬로 조회합니다.

    일부 아이템 조회 실패 시 해당 건만 건너뜁니다(파이프라인은 계속).
    """
    r = await client.get(f"{HN_BASE}/topstories.json", timeout=30.0)
    r.raise_for_status()
    ids: list[int] = r.json()[:top_n]

    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_one(item_id: int) -> RawCollectedItem | None:
        async with semaphore:
            try:
                ir = await client.get(f"{HN_BASE}/item/{item_id}.json", timeout=15.0)
                ir.raise_for_status()
                data = ir.json()
            except (httpx.HTTPError, ValueError, TypeError):
                return None
        if not data or data.get("type") != "story":
            return None
        url = data.get("url") or f"https://news.ycombinator.com/item?id={item_id}"
        title = (data.get("title") or "").strip() or "(no title)"
        text = (data.get("text") or "")[:8000]
        score = data.get("score")
        published = _parse_hn_time(data.get("time"))
        payload: dict[str, Any] = {
            "hn_id": item_id,
            "score": score if isinstance(score, int) else 0,
            "by": data.get("by"),
        }
        return RawCollectedItem(
            source="hackernews",
            source_name="Hacker News",
            title=title,
            url=url,
            published_at=published,
            raw_text=text,
            raw_payload=payload,
        )

    tasks = [fetch_one(i) for i in ids]
    results = await asyncio.gather(*tasks)
    return [x for x in results if x is not None]
