"""Discord Incoming Webhook 비동기 전송."""

import httpx

from app.core.exceptions import DiscordDeliveryError


def format_discord_content(
    *,
    summary: str,
    top_items: list[tuple[str, str]],
    routine_type: str,
    run_label: str,
) -> str:
    """Discord 메시지 본문 (마크다운 단순 텍스트)."""
    lines = [
        f"**트렌드 다이제스트** `{routine_type}` — {run_label}",
        "",
        summary,
        "",
        "**Top 3**",
    ]
    for i, (title, url) in enumerate(top_items[:3], start=1):
        lines.append(f"{i}. [{title}]({url})")
    return "\n".join(lines)


async def send_discord_webhook(
    client: httpx.AsyncClient,
    webhook_url: str,
    content: str,
) -> None:
    """
    Discord webhook으로 JSON POST.

    Raises:
        DiscordDeliveryError: HTTP 오류 또는 비정상 응답 시.
    """
    resp = await client.post(
        webhook_url,
        json={"content": content[:2000]},
        headers={"Content-Type": "application/json"},
        timeout=30.0,
    )
    if resp.status_code < 200 or resp.status_code >= 300:
        raise DiscordDeliveryError(
            f"Discord webhook 실패: HTTP {resp.status_code} {resp.text[:200]}",
            status_code=resp.status_code,
        )
