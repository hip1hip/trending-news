"""initial tables

Revision ID: 20260408_0001
Revises:
Create Date: 2026-04-08

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260408_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "source_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_name", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("url_hash", sa.String(length=64), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url", name="uq_source_items_url"),
        sa.UniqueConstraint("url_hash", name="uq_source_items_url_hash"),
    )
    op.create_index("ix_source_items_url_hash", "source_items", ["url_hash"], unique=False)

    op.create_table(
        "normalized_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_item_id", sa.Integer(), nullable=False),
        sa.Column("normalized_title", sa.String(length=512), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("importance_score", sa.Float(), nullable=False),
        sa.Column("duplicate_group_key", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_item_id"], ["source_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_normalized_items_duplicate_group",
        "normalized_items",
        ["duplicate_group_key"],
        unique=False,
    )

    op.create_table(
        "digests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("routine_type", sa.String(length=64), nullable=False),
        sa.Column("run_date", sa.Date(), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "digest_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("digest_id", sa.Integer(), nullable=False),
        sa.Column("normalized_item_id", sa.Integer(), nullable=False),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["digest_id"], ["digests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["normalized_item_id"], ["normalized_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("digest_id", "rank_order", name="uq_digest_items_digest_rank"),
    )

    op.create_table(
        "job_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("job_runs")
    op.drop_table("digest_items")
    op.drop_table("digests")
    op.drop_index("ix_normalized_items_duplicate_group", table_name="normalized_items")
    op.drop_table("normalized_items")
    op.drop_index("ix_source_items_url_hash", table_name="source_items")
    op.drop_table("source_items")
