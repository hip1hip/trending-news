"""SQLAlchemy 선언적 베이스."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """ORM 모델 공통 베이스."""
