"""정규화 제목 기반 중복 그룹 키 (동일 이슈 다른 URL 병합)."""

import hashlib

from app.normalization.title import normalize_title


def compute_duplicate_group_key(title: str) -> str:
    """
    정규화된 제목의 해시를 그룹 키로 사용합니다.

    url_hash와 별도로 '같은 제목' 후보를 한 그룹으로 묶을 때 사용합니다.
    """
    nt = normalize_title(title)
    return hashlib.sha256(nt.encode("utf-8")).hexdigest()[:40]
