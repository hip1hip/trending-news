"""Discord Incoming Webhook 비동기 전송 (임베드·중복 억제)."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

import httpx

from app.core.exceptions import DiscordDeliveryError
from app.summarization.mock_summarizer import SummaryPayload

# 동일 페이로드를 짧은 시간에 두 번 보내는 경우(이중 POST 등) 방지
_last_payload_fingerprint: str | None = None
_last_payload_time: float = 0.0
_DEDUP_WINDOW_SEC = 90.0


def _fingerprint_payload(payload: dict[str, Any]) -> str:
    """JSON 정규화 후 해시."""
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_discord_webhook_payload(
    *,
    summary_payload: SummaryPayload,
    routine_type: str,
    run_label: str,
) -> dict[str, Any]:
    """
    한국어 요약 + 항목별 요약 + 원문 링크(미리보기 억제용 <>).

    Discord 임베드 필드 값은 1024자 제한이 있어 잘라냅니다.
    """
    summary = summary_payload["summary"][:4096]
    fields: list[dict[str, Any]] = []
    for i, it in enumerate(summary_payload["items"][:3], start=1):
        title = (it.get("title") or "(제목 없음)")[:200]
        takeaway = (it.get("takeaway") or "")[:700]
        url = (it.get("url") or "").strip()
        # <> 로 감싸면 클라이언트에서 링크 미리보기가 대부분 억제됨
        link_line = f"원문: <{url}>" if url else "원문: (없음)"
        value = f"{takeaway}\n{link_line}"
        if len(value) > 1024:
            value = value[:1021] + "…"
        fields.append({"name": f"{i}. {title}", "value": value, "inline": False})

    embed: dict[str, Any] = {
        "title": f"트렌드 다이제스트 ({routine_type})",
        "description": summary,
        "color": 0x5865F2,
        "fields": fields,
    }
    if run_label:
        embed["footer"] = {"text": run_label[:2048]}

    return {
        "username": "Trend Digest",
        "embeds": [embed],
    }


async def send_discord_webhook(
    client: httpx.AsyncClient,
    webhook_url: str,
    payload: dict[str, Any],
) -> None:
    """
    Discord webhook POST.

    직전과 동일한 본문을 `_DEDUP_WINDOW_SEC` 안에 다시내려 하면 생략합니다.
    """
    global _last_payload_fingerprint, _last_payload_time

    fp = _fingerprint_payload(payload)
    now = time.monotonic()
    if (
        _last_payload_fingerprint == fp
        and (now - _last_payload_time) < _DEDUP_WINDOW_SEC
    ):
        return

    resp = await client.post(
        webhook_url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=60.0,
    )
    if resp.status_code < 200 or resp.status_code >= 300:
        raise DiscordDeliveryError(
            f"Discord webhook 실패: HTTP {resp.status_code} {resp.text[:200]}",
            status_code=resp.status_code,
        )

    _last_payload_fingerprint = fp
    _last_payload_time = now
