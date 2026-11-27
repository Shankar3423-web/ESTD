"""Add radar_drops table for dynamic Weekly Radar upcoming events.

Revision ID: 0007_add_radar_drops
Revises: 0006_add_estdpod_episodes
Create Date: 2026-11-27 12:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0007_add_radar_drops"
down_revision: Union[str, None] = "0006_add_estdpod_episodes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "radar_drops" not in existing_tables:
        op.create_table(
            "radar_drops",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("drop_key", sa.String(length=128), nullable=False),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("category", sa.String(length=100), nullable=False),
            sa.Column("tag", sa.String(length=100), nullable=False, server_default="Upcoming Event"),
            sa.Column("event_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "source_article_id",
                sa.BigInteger(),
                sa.ForeignKey("news_articles.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("source_title", sa.Text(), nullable=True),
            sa.Column("source_url", sa.Text(), nullable=True),
            sa.Column("source_name", sa.String(length=255), nullable=True),
            sa.Column("confidence", sa.Integer(), nullable=False, server_default="85"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column(
                "generated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
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
            sa.UniqueConstraint("drop_key", name="uq_radar_drops_drop_key"),
        )
        op.create_index("ix_radar_drops_drop_key", "radar_drops", ["drop_key"])
        op.create_index("ix_radar_drops_category", "radar_drops", ["category"])
        op.create_index("ix_radar_drops_event_date", "radar_drops", ["event_date"])
        op.create_index("ix_radar_drops_source_article_id", "radar_drops", ["source_article_id"])
        op.create_index("ix_radar_drops_is_active", "radar_drops", ["is_active"])
        op.create_index("ix_radar_drops_active_event_date", "radar_drops", ["is_active", "event_date"])
        op.create_index("ix_radar_drops_category_active", "radar_drops", ["category", "is_active"])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "radar_drops" in existing_tables:
        op.drop_table("radar_drops")
