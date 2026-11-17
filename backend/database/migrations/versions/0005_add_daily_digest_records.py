"""Add daily_digest_records table for Plan C Daily Category Digest exports.

Revision ID: 0005_add_daily_digest_records
Revises: 0004_add_slug_qa_status
Create Date: 2026-11-16 16:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0005_add_daily_digest_records"
down_revision: Union[str, None] = "0004_add_slug_qa_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "daily_digest_records" not in existing_tables:
        op.create_table(
            "daily_digest_records",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("digest_date", sa.Date(), nullable=False),
            sa.Column("category", sa.String(length=100), nullable=False),
            sa.Column("article_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("google_document_id", sa.String(length=255), nullable=True),
            sa.Column("google_document_url", sa.Text(), nullable=True),
            sa.Column("google_drive_folder_id", sa.String(length=255), nullable=True),
            sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
            sa.Column("error_message", sa.Text(), nullable=True),
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
            sa.UniqueConstraint("digest_date", "category", name="uq_daily_digest_date_category"),
        )
        op.create_index(
            "ix_daily_digest_records_id",
            "daily_digest_records",
            ["id"],
            unique=False,
        )
        op.create_index(
            "ix_daily_digest_records_digest_date",
            "daily_digest_records",
            ["digest_date"],
            unique=False,
        )
        op.create_index(
            "ix_daily_digest_records_category",
            "daily_digest_records",
            ["category"],
            unique=False,
        )
        op.create_index(
            "ix_daily_digest_date_cat",
            "daily_digest_records",
            ["digest_date", "category"],
            unique=False,
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "daily_digest_records" in existing_tables:
        op.drop_table("daily_digest_records")

