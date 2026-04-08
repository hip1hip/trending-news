"""수집기 공통 타입."""

from datetime import datetime
from typing import Any, TypedDict


class RawCollectedItem(TypedDict, total=False):
    """수집기가 반환하는 정규화 전 dict."""

    source: str
    source_name: str
    title: str
    url: str
    published_at: datetime | str | None
    raw_text: str
    raw_payload: dict[str, Any]
