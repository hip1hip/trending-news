"""도메인·HTTP 예외 (필요 시 확장)."""

from fastapi import HTTPException, status


class DiscordDeliveryError(Exception):
    """Discord 웹훅 전송 실패."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def not_found(detail: str = "리소스를 찾을 수 없습니다.") -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
