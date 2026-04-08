"""Upstage Solar (OpenAI 호환) 채팅 API로 한국어 요약 생성."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.summarization.mock_summarizer import SummaryItemOut, SummaryPayload

def _extract_json_object(text: str) -> dict[str, Any]:
    """모델 응답에서 JSON 객체를 파싱 (코드 펜스 허용)."""
    raw = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if fence:
        raw = fence.group(1).strip()
    return json.loads(raw)


def _fallback_from_parse_error(
    items_input: list[tuple[str, str, str, float]],
    raw_text: str,
) -> SummaryPayload:
    """파싱 실패 시 안전한 한국어 플레이스홀더."""
    summary = (
        "LLM 응답을 JSON으로 파싱하지 못했습니다. 아래는 원문 제목만 정리합니다."
        if items_input
        else "요약 생성에 실패했습니다."
    )
    out_items: list[SummaryItemOut] = []
    for title, url, _, score in items_input[:5]:
        out_items.append(
            SummaryItemOut(
                title=title,
                url=url,
                takeaway=f"(파싱 실패) 점수 {score:.1f} — 원문 제목 그대로 표시",
            )
        )
    return SummaryPayload(summary=summary, items=out_items)


async def summarize_with_upstage(
    client: httpx.AsyncClient,
    *,
    api_key: str,
    model: str,
    base_url: str,
    ranked: list[tuple[str, str, str, float]],
) -> SummaryPayload:
    """
    상위 항목 (영문 title, url, 본문 스니펫, score)을 한국어 요약으로 변환.

    모델 출력은 반드시 JSON 한 덩어리여야 합니다.
    """
    if not ranked:
        return SummaryPayload(summary="이번 런에서 수집된 항목이 없습니다.", items=[])

    lines = []
    for i, (title, url, snippet, score) in enumerate(ranked, start=1):
        lines.append(
            f"{i}. title: {title}\n   url: {url}\n   score: {score:.2f}\n"
            f"   snippet: {(snippet or '')[:1200]}"
        )
    block = "\n".join(lines)

    system = (
        "당신은 기술 뉴스 에디터입니다. 입력은 영어 제목·URL·짧은 본문 스니펫입니다. "
        "반드시 아래 스키마의 JSON만 출력하세요. 마크다운·설명 문장 금지."
    )
    schema_hint = """{
  "summary_ko": "전체 흐름을 2~4문장 한국어로",
  "items": [
    {
      "title_ko": "한국어 제목 (읽기 쉽게)",
      "summary_ko": "핵심을 2~3문장 한국어로",
      "url": "원본과 동일한 URL",
      "title_en": "원문 영어 제목 (참고용)"
    }
  ]
}"""
    user = (
        f"다음 {len(ranked)}개 기사를 한국어로 요약해 주세요.\n\n"
        f"{block}\n\n"
        f"출력 JSON 스키마 예시:\n{schema_hint}\n"
        "items 배열 길이는 입력 개수와 같아야 합니다. 순서도 동일하게 유지하세요."
    )

    url = f"{base_url.rstrip('/')}/chat/completions"
    resp = await client.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.35,
            "response_format": {"type": "json_object"},
        },
        timeout=120.0,
    )
    resp.raise_for_status()
    data = resp.json()
    try:
        choice = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return _fallback_from_parse_error(ranked, json.dumps(data)[:800])
    if not choice or not isinstance(choice, str):
        return _fallback_from_parse_error(ranked, "")
    try:
        parsed = _extract_json_object(choice)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return _fallback_from_parse_error(ranked, choice)

    summary_ko = str(parsed.get("summary_ko", "")).strip() or "요약을 생성하지 못했습니다."
    raw_items = parsed.get("items")
    if not isinstance(raw_items, list):
        return _fallback_from_parse_error(ranked, choice)

    out_items: list[SummaryItemOut] = []
    for i in range(len(ranked)):
        title_en, url_en, _, _ = ranked[i]
        row_raw = raw_items[i] if i < len(raw_items) else {}
        row = row_raw if isinstance(row_raw, dict) else {}
        url_out = str(row.get("url", url_en)).strip() or url_en
        title_ko = str(row.get("title_ko", "")).strip() or title_en
        summary_item = str(row.get("summary_ko", "")).strip()
        title_en_field = str(row.get("title_en", "")).strip() or title_en
        takeaway = summary_item
        if title_en_field and title_en_field != title_ko:
            takeaway = (
                f"{summary_item}\n(원제목: {title_en_field})" if summary_item else f"(원제목: {title_en_field})"
            )
        out_items.append(
            SummaryItemOut(
                title=title_ko,
                url=url_out,
                takeaway=takeaway or "요약 없음",
            )
        )

    return SummaryPayload(summary=summary_ko, items=out_items)
