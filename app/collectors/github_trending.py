"""GitHub Trending — MVP는 결정적 mock 데이터."""

from datetime import UTC, datetime

from app.collectors.base import RawCollectedItem


def collect_github_trending_mock() -> list[RawCollectedItem]:
    """
    실제 스크래핑 대신 항상 동일한 더미 레코드를 반환합니다.

    운영에서 실제 HTML 파싱을 붙일 때 이 함수를 교체·확장하면 됩니다.
    """
    now = datetime.now(tz=UTC)
    return [
        RawCollectedItem(
            source="github",
            source_name="GitHub Trending (mock)",
            title="awesome-llm — LLM 리소스 모음",
            url="https://github.com/example/awesome-llm",
            published_at=now,
            raw_text="Curated list of LLM tools and papers (mock).",
            raw_payload={"mock": True, "stars": 1200},
        ),
        RawCollectedItem(
            source="github",
            source_name="GitHub Trending (mock)",
            title="fastapi-realworld — FastAPI 예제 앱",
            url="https://github.com/example/fastapi-realworld",
            published_at=now,
            raw_text="Production-style FastAPI template (mock).",
            raw_payload={"mock": True, "stars": 800},
        ),
        RawCollectedItem(
            source="github",
            source_name="GitHub Trending (mock)",
            title="pytorch-tutorials — 딥러닝 튜토리얼",
            url="https://github.com/example/pytorch-tutorials",
            published_at=now,
            raw_text="Educational notebooks (mock).",
            raw_payload={"mock": True, "stars": 2400},
        ),
    ]
