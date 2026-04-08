"""제목 정규화: 소문자, 공백·기호 단순 제거."""

import re


def normalize_title(title: str) -> str:
    """소문자, 앞뒤 공백 제거, 비문자를 공백으로 치환 후 연속 공백 축소."""
    t = title.lower().strip()
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)
    t = re.sub(r"\s+", " ", t).strip()
    return t or "(empty)"
