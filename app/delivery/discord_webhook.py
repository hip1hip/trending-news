"""Discord Incoming Webhook 비동기 전송 (긴 요약·다중 임베드·분할 POST)."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

import httpx

from app.core.exceptions import DiscordDeliveryError
from app.summarization.mock_summarizer import SummaryPayload

# Discord: 모든 embed 합산 약 6000자 제한 — 여유 두고 배치
_DISCORD_EMBED_BATCH_CHAR_BUDGET = 5500
_DEDUP_WINDOW_SEC = 90.0

_last_payload_fingerprint: str | None = None
_last_payload_time: float = 0.0


def _fingerprint_payloads(payloads: list[dict[str, Any]]) -> str:
    canonical = json.dumps(payloads, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _embed_size(embed: dict[str, Any]) -> int:
    """대략적인 문자 수(디스코드 제한 추정용)."""
    n = len(embed.get("title") or "")
    n += len(embed.get("description") or "")
    ft = embed.get("footer")
    if isinstance(ft, dict):
        n += len(ft.get("text") or "")
    return n + 80


def build_discord_webhook_payloads(
    *,
    summary_payload: SummaryPayload,
    routine_type: str,
    run_label: str,
) -> list[dict[str, Any]]:
    """
    전체 요약(최대 4096) + 항목별 임베드(각 설명 최대 4096).

    한 메시지에 너무 길면 여러 번 webhook POST 로 나눕니다.
    """
    summary_full = (summary_payload["summary"] or "")[:4096]
    header_embed: dict[str, Any] = {
        "title": f"트렌드 다이제스트 ({routine_type}) — 전체 요약",
        "description": summary_full,
        "color": 0x5865F2,
    }

    item_embeds: list[dict[str, Any]] = []
    for i, it in enumerate(summary_payload["items"][:3], start=1):
        title = (it.get("title") or "(제목 없음)")[:250]
        takeaway = it.get("takeaway") or ""
        url = (it.get("url") or "").strip()
        desc = f"{takeaway}\n\n원문: <{url}>" if url else takeaway
        if len(desc) > 4096:
            desc = desc[:4093] + "…"
        item_embeds.append(
            {
                "title": f"{i}. {title}",
                "description": desc,
                "color": 0x57F287,
            }
        )

    all_embeds = [header_embed, *item_embeds]
    batches: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    total = 0

    for emb in all_embeds:
        sz = _embed_size(emb)
        if current and total + sz > _DISCORD_EMBED_BATCH_CHAR_BUDGET:
            batches.append(current)
            current = []
            total = 0
        current.append(emb)
        total += sz
    if current:
        batches.append(current)

    payloads: list[dict[str, Any]] = []
    for batch in batches:
        payloads.append({"username": "Trend Digest", "embeds": batch})

    if payloads and run_label:
        payloads[-1]["embeds"][-1]["footer"] = {"text": run_label[:2048]}

    return payloads


async def send_discord_webhooks(
    client: httpx.AsyncClient,
    webhook_url: str,
    payloads: list[dict[str, Any]],
) -> None:
    """
    여러 webhook 페이로드를 순서대로 전송.

    직전과 동일한 페이로드 시퀀스가 `_DEDUP_WINDOW_SEC` 안에 반복되면 생략합니다.
    """
    global _last_payload_fingerprint, _last_payload_time

    if not payloads:
        return

    fp = _fingerprint_payloads(payloads)
    now = time.monotonic()
    if (
        _last_payload_fingerprint == fp
        and (now - _last_payload_time) < _DEDUP_WINDOW_SEC
    ):
        return

    for payload in payloads:
        resp = await client.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=90.0,
        )
        if resp.status_code < 200 or resp.status_code >= 300:
            raise DiscordDeliveryError(
                f"Discord webhook 실패: HTTP {resp.status_code} {resp.text[:200]}",
                status_code=resp.status_code,
            )

    _last_payload_fingerprint = fp
    _last_payload_time = now
