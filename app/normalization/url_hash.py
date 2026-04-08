"""URL 정규화 및 SHA-256 해시 (url_hash / 유니크용)."""

import hashlib
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def normalize_url(url: str) -> str:
    """
    스킴·호스트 소문자, 프래그먼트 제거, 쿼리 키 정렬, 트레일링 슬래시 정리.

    pathlib은 URL에 부적합하므로 urllib만 사용합니다.
    """
    raw = url.strip()
    p = urlparse(raw)
    scheme = (p.scheme or "http").lower()
    netloc = p.netloc.lower()
    path = p.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    q_pairs = sorted(parse_qsl(p.query, keep_blank_values=True))
    query = urlencode(q_pairs)
    normalized = urlunparse((scheme, netloc, path, "", query, ""))
    return normalized


def hash_url(url: str) -> str:
    """정규화 URL의 SHA-256 hex."""
    n = normalize_url(url)
    return hashlib.sha256(n.encode("utf-8")).hexdigest()
