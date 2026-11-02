"""Create Step 5 knowledge source tables and seed canonical categories.

Revision ID: 0001_create_step5_tables
Revises: 
Create Date: 2026-10-05 12:00:00.000000

"""
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_create_step5_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The 5 canonical ESTD categories
CANONICAL_CATEGORIES = [
    {"name": "Artificial Intelligence", "slug": "artificial-intelligence"},
    {"name": "Technology", "slug": "technology"},
    {"name": "Business", "slug": "business"},
    {"name": "Education", "slug": "education"},
    {"name": "Science", "slug": "science"},
]


def upgrade() -> None:
    # 1. Create categories table
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_categories_name"),
        sa.UniqueConstraint("slug", name="uq_categories_slug"),
    )
    op.create_index("ix_categories_id", "categories", ["id"], unique=False)
    op.create_index("ix_categories_name", "categories", ["name"], unique=True)
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)

    # 2. Seed the 5 canonical categories deterministically
    categories_table = sa.table(
        "categories",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("slug", sa.String),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    now_utc = datetime.now(timezone.utc)
    for cat in CANONICAL_CATEGORIES:
        op.execute(
            sa.text(
                "INSERT INTO categories (name, slug, created_at) "
                "VALUES (:name, :slug, :created_at) "
                "ON CONFLICT (name) DO NOTHING;"
            ).bindparams(
                name=cat["name"],
                slug=cat["slug"],
                created_at=now_utc,
            )
        )

    # 3. Create news_articles table
    op.create_table(
        "news_articles",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("normalized_url", sa.String(length=1024), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=True),
        sa.Column("source_type", sa.String(length=100), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], name="fk_news_articles_category_id", ondelete="RESTRICT"),
        sa.UniqueConstraint("normalized_url", name="uq_news_articles_normalized_url"),
        sa.UniqueConstraint("content_hash", name="uq_news_articles_content_hash"),
        sa.CheckConstraint("length(trim(title)) > 0", name="ck_news_articles_title_not_empty"),
        sa.CheckConstraint("length(trim(url)) > 0", name="ck_news_articles_url_not_empty"),
        sa.CheckConstraint("length(trim(content)) > 0", name="ck_news_articles_content_not_empty"),
        sa.CheckConstraint(
            "category IN ('Artificial Intelligence', 'Technology', 'Business', 'Education', 'Science')",
            name="ck_news_articles_valid_category",
        ),
    )
    op.create_index("ix_news_articles_id", "news_articles", ["id"], unique=False)
    op.create_index("ix_news_articles_normalized_url", "news_articles", ["normalized_url"], unique=True)
    op.create_index("ix_news_articles_content_hash", "news_articles", ["content_hash"], unique=True)
    op.create_index("ix_news_articles_category", "news_articles", ["category"], unique=False)
    op.create_index("ix_news_articles_category_id", "news_articles", ["category_id"], unique=False)
    op.create_index("ix_news_articles_source_name", "news_articles", ["source_name"], unique=False)
    op.create_index("ix_news_articles_source_type", "news_articles", ["source_type"], unique=False)
    op.create_index("ix_news_articles_published_at", "news_articles", ["published_at"], unique=False)
    op.create_index("ix_news_articles_created_at", "news_articles", ["created_at"], unique=False)
    op.create_index("ix_news_articles_cat_pub", "news_articles", ["category", "published_at"], unique=False)
    op.create_index("ix_news_articles_source_pub", "news_articles", ["source_name", "published_at"], unique=False)

    # 4. Create estd_duplicate_index if not exists
    op.execute("""
        CREATE TABLE IF NOT EXISTS estd_duplicate_index (
            id SERIAL PRIMARY KEY,
            article_id VARCHAR(255),
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            normalized_url VARCHAR(1024) NOT NULL,
            content_hash VARCHAR(64) NOT NULL,
            category VARCHAR(100) NOT NULL,
            source_name VARCHAR(255),
            source_type VARCHAR(100) NOT NULL,
            author VARCHAR(255),
            published_at VARCHAR(100),
            content_preview TEXT,
            cleaned_content TEXT,
            is_duplicate BOOLEAN NOT NULL DEFAULT FALSE,
            duplicate_reason VARCHAR(50),
            matched_record_id INTEGER,
            similarity_score FLOAT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS ix_estd_duplicate_index_id ON estd_duplicate_index (id);
        CREATE INDEX IF NOT EXISTS ix_estd_duplicate_index_article_id ON estd_duplicate_index (article_id);
        CREATE INDEX IF NOT EXISTS ix_estd_duplicate_index_normalized_url ON estd_duplicate_index (normalized_url);
        CREATE INDEX IF NOT EXISTS ix_estd_duplicate_index_content_hash ON estd_duplicate_index (content_hash);
        CREATE INDEX IF NOT EXISTS ix_estd_duplicate_index_category ON estd_duplicate_index (category);
        CREATE INDEX IF NOT EXISTS ix_estd_duplicate_index_is_duplicate ON estd_duplicate_index (is_duplicate);
        CREATE INDEX IF NOT EXISTS ix_estd_duplicate_index_created_at ON estd_duplicate_index (created_at);
        CREATE INDEX IF NOT EXISTS ix_estd_dup_url_hash ON estd_duplicate_index (normalized_url, content_hash);
        CREATE INDEX IF NOT EXISTS ix_estd_dup_cat_created ON estd_duplicate_index (category, created_at);
    """)


def downgrade() -> None:
    op.drop_table("news_articles")
    op.drop_table("categories")
    op.execute("DROP TABLE IF EXISTS estd_duplicate_index;")
