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
            f"   snippet: {(snippet or '')[:2500]}"
        )
    block = "\n".join(lines)

    system = (
        "당신은 기술·AI 트렌드 에디터입니다. 독자가 원문 링크를 열지 않아도 맥락을 이해할 수 있게 "
        "한국어로 충분히 길고 구체적으로 쓰세요. 반드시 아래 스키마의 JSON만 출력하세요. "
        "마크다운 코드펜스·추가 설명 금지."
    )
    schema_hint = """{
  "summary_ko": "전체 트렌드를 8~15문장(또는 약 700~1500자) 한국어로. 각 기사가 왜 묶였는지·공통 주제·시사점 포함",
  "items": [
    {
      "title_ko": "한국어 제목 (읽기 쉽게)",
      "summary_ko": "이 기사만 5~12문장(또는 약 400~1200자) 한국어: 배경, 핵심 내용, 왜 중요한지, 누가 관련되는지",
      "url": "원본과 동일한 URL",
      "title_en": "원문 영어 제목 (참고용)"
    }
  ]
}"""
    user = (
        f"다음 {len(ranked)}개 기사를 한국어로 깊게 요약해 주세요. 원문을 읽지 않은 사람도 "
        f"트렌드를 이해할 수 있을 정도로 상세히 쓰세요.\n\n"
        f"{block}\n\n"
        f"출력 JSON 스키마 예시:\n{schema_hint}\n"
        "items 배열 길이는 입력 개수와 같아야 하고 순서도 동일해야 합니다."
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
            "max_tokens": 8192,
            "response_format": {"type": "json_object"},
        },
        timeout=180.0,
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
