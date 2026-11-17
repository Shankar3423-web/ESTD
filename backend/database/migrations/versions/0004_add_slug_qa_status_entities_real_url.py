"""Add slug, canonical_url, source_published_at, entities, and qa_status to news_articles.

Revision ID: 0004_add_slug_qa_status
Revises: 0003_upgrade_taxonomy
Create Date: 2026-11-16 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column, select
from backend.common.utils.slug_utils import generate_slug

# revision identifiers, used by Alembic.
revision: str = "0004_add_slug_qa_status"
down_revision: Union[str, None] = "0003_upgrade_taxonomy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Add new columns safely (check if already exists in case of manual SQL)
    inspector = sa.inspect(conn)
    existing_columns = [c["name"] for c in inspector.get_columns("news_articles")]

    if "slug" not in existing_columns:
        op.add_column("news_articles", sa.Column("slug", sa.String(length=320), nullable=True))

    if "canonical_url" not in existing_columns:
        op.add_column("news_articles", sa.Column("canonical_url", sa.Text(), nullable=True))

    if "source_published_at" not in existing_columns:
        op.add_column("news_articles", sa.Column("source_published_at", sa.DateTime(timezone=True), nullable=True))

    if "entities" not in existing_columns:
        op.add_column("news_articles", sa.Column("entities", sa.JSON(), nullable=True))

    if "qa_status" not in existing_columns:
        op.add_column(
            "news_articles",
            sa.Column("qa_status", sa.String(length=32), server_default="PUBLISHED", nullable=False),
        )

    # 2. Backfill existing records with slugs, default entities, and canonical_url
    news_articles_table = table(
        "news_articles",
        column("id", sa.BigInteger),
        column("title", sa.Text),
        column("url", sa.Text),
        column("slug", sa.String),
        column("canonical_url", sa.Text),
        column("entities", sa.JSON),
        column("qa_status", sa.String),
    )

    rows = conn.execute(select(news_articles_table.c.id, news_articles_table.c.title, news_articles_table.c.url, news_articles_table.c.slug)).fetchall()
    
    for row in rows:
        art_id = row[0]
        title = row[1] or ""
        url = row[2] or ""
        existing_slug = row[3]

        if not existing_slug:
            new_slug = generate_slug(title, str(art_id))
            conn.execute(
                news_articles_table.update()
                .where(news_articles_table.c.id == art_id)
                .values(
                    slug=new_slug,
                    canonical_url=url,
                    entities={},
                    qa_status="PUBLISHED",
                )
            )

    # 3. Create indices and unique constraint on slug
    existing_indexes = [idx["name"] for idx in inspector.get_indexes("news_articles")]
    if "ix_news_articles_slug" not in existing_indexes:
        op.create_index("ix_news_articles_slug", "news_articles", ["slug"], unique=True)

    if "ix_news_articles_qa_status" not in existing_indexes:
        op.create_index("ix_news_articles_qa_status", "news_articles", ["qa_status"], unique=False)

    if "ix_news_articles_source_published_at" not in existing_indexes:
        op.create_index("ix_news_articles_source_published_at", "news_articles", ["source_published_at"], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_indexes = [idx["name"] for idx in inspector.get_indexes("news_articles")]

    if "ix_news_articles_source_published_at" in existing_indexes:
        op.drop_index("ix_news_articles_source_published_at", table_name="news_articles")
    if "ix_news_articles_qa_status" in existing_indexes:
        op.drop_index("ix_news_articles_qa_status", table_name="news_articles")
    if "ix_news_articles_slug" in existing_indexes:
        op.drop_index("ix_news_articles_slug", table_name="news_articles")

    existing_columns = [c["name"] for c in inspector.get_columns("news_articles")]
    if "qa_status" in existing_columns:
        op.drop_column("news_articles", "qa_status")
    if "entities" in existing_columns:
        op.drop_column("news_articles", "entities")
    if "source_published_at" in existing_columns:
        op.drop_column("news_articles", "source_published_at")
    if "canonical_url" in existing_columns:
        op.drop_column("news_articles", "canonical_url")
    if "slug" in existing_columns:
        op.drop_column("news_articles", "slug")

