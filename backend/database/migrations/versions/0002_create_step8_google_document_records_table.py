"""Create Step 8 Google Document records table for Drive artifact tracking.

Revision ID: 0002_create_step8_tables
Revises: 0001_create_step5_tables
Create Date: 2026-10-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_create_step8_tables"
down_revision: Union[str, None] = "0001_create_step5_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "google_document_records",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("article_id", sa.BigInteger(), nullable=False),
        sa.Column("google_document_id", sa.String(length=255), nullable=True),
        sa.Column("google_document_url", sa.Text(), nullable=True),
        sa.Column("google_drive_root_folder_id", sa.String(length=255), nullable=True),
        sa.Column("google_drive_category_folder_id", sa.String(length=255), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("document_title", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="PENDING", nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["article_id"],
            ["news_articles.id"],
            name="fk_google_doc_article_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("article_id", name="uq_google_doc_article_id"),
        sa.CheckConstraint("length(trim(document_title)) > 0", name="ck_google_doc_title_not_empty"),
        sa.CheckConstraint(
            "status IN ('PENDING', 'CREATED', 'FAILED')",
            name="ck_google_doc_valid_status",
        ),
    )
    op.create_index("ix_google_document_records_id", "google_document_records", ["id"], unique=False)
    op.create_index("ix_google_document_records_article_id", "google_document_records", ["article_id"], unique=True)
    op.create_index("ix_google_document_records_google_document_id", "google_document_records", ["google_document_id"], unique=False)
    op.create_index("ix_google_document_records_category", "google_document_records", ["category"], unique=False)
    op.create_index("ix_google_document_records_status", "google_document_records", ["status"], unique=False)
    op.create_index("ix_google_document_records_created_at", "google_document_records", ["created_at"], unique=False)
    op.create_index("ix_google_doc_cat_status", "google_document_records", ["category", "status"], unique=False)


def downgrade() -> None:
    op.drop_table("google_document_records")
