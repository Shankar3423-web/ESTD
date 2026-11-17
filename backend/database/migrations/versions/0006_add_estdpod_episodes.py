"""Add estdpod_episodes table for ESTDPOD YouTube Channel podcasts and guest spotlights.

Revision ID: 0006_add_estdpod_episodes
Revises: 0005_add_daily_digest_records
Create Date: 2026-11-17 13:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0006_add_estdpod_episodes"
down_revision: Union[str, None] = "0005_add_daily_digest_records"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "estdpod_episodes" not in existing_tables:
        op.create_table(
            "estdpod_episodes",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("youtube_video_id", sa.String(length=64), nullable=False),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("slug", sa.String(length=320), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("thumbnail_url", sa.Text(), nullable=True),
            sa.Column("duration", sa.String(length=32), nullable=True),
            sa.Column("duration_seconds", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("guest_name", sa.String(length=255), nullable=True),
            sa.Column("guest_designation", sa.String(length=255), nullable=True),
            sa.Column("guest_organization", sa.String(length=255), nullable=True),
            sa.Column("guest_avatar_url", sa.Text(), nullable=True),
            sa.Column("category", sa.String(length=100), nullable=False, server_default="Tech"),
            sa.Column("tags", sa.JSON(), nullable=True),
            sa.Column("key_takeaways", sa.JSON(), nullable=True),
            sa.Column("view_count", sa.Integer(), nullable=True, server_default="0"),
            sa.Column("is_featured", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("youtube_video_id", name="uq_estdpod_youtube_video_id"),
            sa.UniqueConstraint("slug", name="uq_estdpod_slug"),
        )
        op.create_index("ix_estdpod_episodes_youtube_video_id", "estdpod_episodes", ["youtube_video_id"])
        op.create_index("ix_estdpod_episodes_slug", "estdpod_episodes", ["slug"])
        op.create_index("ix_estdpod_episodes_published_at", "estdpod_episodes", ["published_at"])
        op.create_index("ix_estdpod_episodes_category", "estdpod_episodes", ["category"])
        op.create_index("ix_estdpod_episodes_is_featured", "estdpod_episodes", ["is_featured"])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "estdpod_episodes" in existing_tables:
        op.drop_table("estdpod_episodes")

