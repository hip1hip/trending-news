"""결정적 목 요약기 — 실제 LLM 호출 없음."""

from typing import TypedDict


class SummaryItemOut(TypedDict):
    """요약 블록 내 단일 항목."""

    title: str
    url: str
    takeaway: str


class SummaryPayload(TypedDict):
    """다이제스트 요약 결과."""

    summary: str
    items: list[SummaryItemOut]


def summarize_digest_mock(
    ranked: list[tuple[str, str, float]],
) -> SummaryPayload:
    """
    상위 (title, url, score) 튜플 목록으로 고정 규칙 요약을 생성합니다.

    동일 입력이면 항상 동일 출력이 나오도록 문자열만 조합합니다.
    """
    if not ranked:
        return SummaryPayload(
            summary="이번 런에서 수집된 항목이 없습니다.",
            items=[],
        )
    titles = [t[0] for t in ranked]
    head = " · ".join(titles[:3])
    summary = (
        f"이번 런 주요 토픽(목 요약·LLM 미연동): {head}"
    )
    items: list[SummaryItemOut] = []
    for title, url, score in ranked:
        takeaway = f"[목] 점수 {score:.1f} — 원문 제목: {title[:120]}"
        items.append(SummaryItemOut(title=title, url=url, takeaway=takeaway))
    return SummaryPayload(summary=summary, items=items)
