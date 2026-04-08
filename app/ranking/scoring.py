"""중요도 점수: freshness + keyword + engagement."""

from datetime import UTC, datetime
from typing import Any


def freshness_score(published_at: datetime | None, *, now: datetime) -> float:
    """최근일수록 높음. 최대 약 10점."""
    if published_at is None:
        return 0.0
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=UTC)
    delta_days = (now - published_at).total_seconds() / 86400.0
    return max(0.0, 10.0 - min(delta_days, 10.0))


def keyword_score(title: str, raw_text: str | None) -> float:
    """간단 키워드 매칭 가중치."""
    blob = f"{title} {raw_text or ''}".lower()
    keywords = (
        "ai",
        "llm",
        "gpt",
        "ml",
        "model",
        "neural",
        "openai",
        "api",
        "python",
        "docker",
        "kubernetes",
        "github",
        "security",
    )
    return float(sum(1.5 for k in keywords if k in blob))


def engagement_score(raw_payload: dict[str, Any] | None) -> float:
    """HN score 또는 mock stars 등. 상한 10."""
    if not raw_payload:
        return 0.0
    if "score" in raw_payload and isinstance(raw_payload["score"], int):
        return min(10.0, float(raw_payload["score"]) / 30.0)
    if raw_payload.get("mock") and isinstance(raw_payload.get("stars"), int):
        return min(10.0, float(raw_payload["stars"]) / 300.0)
    return 0.0


def total_importance_score(
    *,
    published_at: datetime | None,
    title: str,
    raw_text: str | None,
    raw_payload: dict[str, Any] | None,
    now: datetime,
) -> float:
    """세 부분 점수 합산."""
    return (
        freshness_score(published_at, now=now)
        + keyword_score(title, raw_text)
        + engagement_score(raw_payload)
    )
