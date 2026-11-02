"""Upgrade taxonomy to canonical five categories and hierarchical subcategories.

Revision ID: 0003_upgrade_taxonomy
Revises: 0002_create_step8_tables
Create Date: 2026-10-09 15:30:00.000000

"""
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003_upgrade_taxonomy"
down_revision: Union[str, None] = "0002_create_step8_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# New 5 canonical categories with stable codes
CANONICAL_CATEGORIES = [
    {"id": 1, "code": "TECH", "name": "Tech", "slug": "tech"},
    {"id": 2, "code": "ENT", "name": "Entertainment", "slug": "entertainment"},
    {"id": 3, "code": "BIZ_FIN", "name": "Business & Finance", "slug": "business-finance"},
    {"id": 4, "code": "DEV", "name": "Developments", "slug": "developments"},
    {"id": 5, "code": "SPORTS", "name": "Sports", "slug": "sports"},
]

# Canonical subcategories
CANONICAL_SUBCATEGORIES = [
    # 1. Entertainment (ENT - ID 2)
    {"cat_id": 2, "code": "ENT_MOVIES", "name": "Movies & Cinema", "slug": "movies-cinema"},
    {"cat_id": 2, "code": "ENT_MUSIC", "name": "Music", "slug": "music"},
    {"cat_id": 2, "code": "ENT_TV_OTT", "name": "TV & OTT", "slug": "tv-ott"},
    {"cat_id": 2, "code": "ENT_CREATORS", "name": "Creators & Influencers", "slug": "creators-influencers"},
    {"cat_id": 2, "code": "ENT_CELEBS", "name": "Celebrities & Pop Culture", "slug": "celebrities-pop-culture"},
    {"cat_id": 2, "code": "ENT_GAMING", "name": "Gaming & Digital Entertainment", "slug": "gaming-digital-entertainment"},
    {"cat_id": 2, "code": "ENT_AWARDS", "name": "Awards & Events", "slug": "awards-events"},
    {"cat_id": 2, "code": "ENT_DIGITAL_CULTURE", "name": "Digital Storytelling & Culture", "slug": "digital-storytelling-culture"},

    # 2. Sports (SPORTS - ID 5)
    {"cat_id": 5, "code": "SPORTS_CRICKET", "name": "Cricket", "slug": "cricket"},
    {"cat_id": 5, "code": "SPORTS_FOOTBALL", "name": "Football", "slug": "football"},
    {"cat_id": 5, "code": "SPORTS_TENNIS", "name": "Tennis", "slug": "tennis"},
    {"cat_id": 5, "code": "SPORTS_BADMINTON", "name": "Badminton", "slug": "badminton"},
    {"cat_id": 5, "code": "SPORTS_MOTORSPORT", "name": "Motorsport", "slug": "motorsport"},
    {"cat_id": 5, "code": "SPORTS_HOCKEY", "name": "Hockey", "slug": "hockey"},
    {"cat_id": 5, "code": "SPORTS_ATHLETICS", "name": "Athletics & Olympic Sports", "slug": "athletics-olympics"},
    {"cat_id": 5, "code": "SPORTS_ESPORTS", "name": "Esports & Competitive Gaming", "slug": "esports-competitive-gaming"},
    {"cat_id": 5, "code": "SPORTS_OTHER", "name": "Other Sports", "slug": "other-sports"},

    # 3. Tech (TECH - ID 1)
    {"cat_id": 1, "code": "TECH_AI", "name": "Artificial Intelligence", "slug": "artificial-intelligence"},
    {"cat_id": 1, "code": "TECH_SOFTWARE_CLOUD", "name": "Software & Cloud", "slug": "software-cloud"},
    {"cat_id": 1, "code": "TECH_CONSUMER_GADGETS", "name": "Consumer Technology & Gadgets", "slug": "consumer-technology-gadgets"},
    {"cat_id": 1, "code": "TECH_CYBERSECURITY", "name": "Cybersecurity & Privacy", "slug": "cybersecurity-privacy"},
    {"cat_id": 1, "code": "TECH_DEV_TOOLS", "name": "Developer Technologies & Open Source", "slug": "developer-technologies"},
    {"cat_id": 1, "code": "TECH_EMERGING_HARDWARE", "name": "Emerging Tech & Semiconductors", "slug": "emerging-tech-semiconductors"},
    {"cat_id": 1, "code": "TECH_PLATFORMS", "name": "Digital Platforms & Big Tech", "slug": "digital-platforms"},

    # 4. Developments (DEV - ID 4)
    {"cat_id": 4, "code": "DEV_GOV_POLICY", "name": "Government & Public Policy", "slug": "government-public-policy"},
    {"cat_id": 4, "code": "DEV_INFRA", "name": "Infrastructure & Urban Planning", "slug": "infrastructure-planning"},
    {"cat_id": 4, "code": "DEV_ENERGY_CLIMATE", "name": "Energy, Climate & Environment", "slug": "energy-environment"},
    {"cat_id": 4, "code": "DEV_HEALTH_MED", "name": "Health & Medical Sciences", "slug": "health-medical-sciences"},
    {"cat_id": 4, "code": "DEV_EDUCATION", "name": "Education & Learning Policy", "slug": "education-learning-policy"},
    {"cat_id": 4, "code": "DEV_SCIENCE_RESEARCH", "name": "Science & Research Discoveries", "slug": "science-research"},
    {"cat_id": 4, "code": "DEV_GLOBAL_AFFAIRS", "name": "Global Affairs & Geopolitics", "slug": "global-affairs"},

    # 5. Business & Finance (BIZ_FIN - ID 3)
    {"cat_id": 3, "code": "BIZ_MARKETS", "name": "Financial Markets & Banking", "slug": "financial-markets-banking"},
    {"cat_id": 3, "code": "BIZ_STARTUPS", "name": "Startups & Venture Capital", "slug": "startups-venture-capital"},
    {"cat_id": 3, "code": "BIZ_CORP_STRATEGY", "name": "Corporate Strategy & Earnings", "slug": "corporate-strategy-earnings"},
    {"cat_id": 3, "code": "BIZ_PERSONAL_FINANCE", "name": "Personal Finance & Wealth Management", "slug": "personal-finance-wealth"},
    {"cat_id": 3, "code": "BIZ_MACROECONOMY", "name": "Economy & Macroeconomics", "slug": "economy-macroeconomics"},
    {"cat_id": 3, "code": "BIZ_TRADE_INDUSTRY", "name": "Trade, Supply Chain & Industry", "slug": "trade-industry"},
]


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. Update categories table schema
    # -------------------------------------------------------------------------
    op.add_column("categories", sa.Column("code", sa.String(length=50), nullable=True))
    op.add_column("categories", sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False))
    op.add_column("categories", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))

    # -------------------------------------------------------------------------
    # 2. Update existing category records safely to avoid UK collisions
    # -------------------------------------------------------------------------
    # Temporary rename slugs/names to intermediate placeholders
    for cat in CANONICAL_CATEGORIES:
        op.execute(
            sa.text("UPDATE categories SET name = :temp_name, slug = :temp_slug WHERE id = :id")
            .bindparams(temp_name=f"temp_{cat['id']}", temp_slug=f"temp_{cat['id']}", id=cat["id"])
        )
    # Set final canonical values
    now_utc = datetime.now(timezone.utc)
    for cat in CANONICAL_CATEGORIES:
        op.execute(
            sa.text(
                "UPDATE categories SET code = :code, name = :name, slug = :slug, is_active = true, updated_at = :now WHERE id = :id"
            ).bindparams(
                code=cat["code"],
                name=cat["name"],
                slug=cat["slug"],
                now=now_utc,
                id=cat["id"],
            )
        )

    # Now make code NOT NULL and unique
    op.alter_column("categories", "code", nullable=False)
    op.create_unique_constraint("uq_categories_code", "categories", ["code"])
    op.create_index("ix_categories_code", "categories", ["code"], unique=True)
    op.create_index("ix_categories_is_active", "categories", ["is_active"], unique=False)

    # -------------------------------------------------------------------------
    # 3. Create subcategories table
    # -------------------------------------------------------------------------
    op.create_table(
        "subcategories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], name="fk_subcategories_category_id", ondelete="RESTRICT"),
        sa.UniqueConstraint("code", name="uq_subcategories_code"),
        sa.UniqueConstraint("category_id", "slug", name="uq_subcategories_category_slug"),
        sa.UniqueConstraint("category_id", "name", name="uq_subcategories_category_name"),
    )
    op.create_index("ix_subcategories_id", "subcategories", ["id"], unique=False)
    op.create_index("ix_subcategories_category_id", "subcategories", ["category_id"], unique=False)
    op.create_index("ix_subcategories_code", "subcategories", ["code"], unique=True)
    op.create_index("ix_subcategories_slug", "subcategories", ["slug"], unique=False)

    # Seed subcategories
    for sub in CANONICAL_SUBCATEGORIES:
        op.execute(
            sa.text(
                "INSERT INTO subcategories (category_id, code, name, slug, is_active, created_at, updated_at) "
                "VALUES (:cat_id, :code, :name, :slug, true, :now, :now) "
                "ON CONFLICT (code) DO NOTHING;"
            ).bindparams(
                cat_id=sub["cat_id"],
                code=sub["code"],
                name=sub["name"],
                slug=sub["slug"],
                now=now_utc,
            )
        )

    # -------------------------------------------------------------------------
    # 4. Update news_articles table schema
    # -------------------------------------------------------------------------
    op.add_column("news_articles", sa.Column("subcategory", sa.String(length=100), nullable=True))
    op.add_column("news_articles", sa.Column("subcategory_id", sa.Integer(), nullable=True))
    op.add_column("news_articles", sa.Column("original_source_category", sa.String(length=100), nullable=True))
    op.add_column("news_articles", sa.Column("language", sa.String(length=20), server_default="en", nullable=True))
    op.add_column("news_articles", sa.Column("region", sa.String(length=50), nullable=True))

    op.create_foreign_key(
        "fk_news_articles_subcategory_id",
        "news_articles",
        "subcategories",
        ["subcategory_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_news_articles_subcategory", "news_articles", ["subcategory"], unique=False)
    op.create_index("ix_news_articles_subcategory_id", "news_articles", ["subcategory_id"], unique=False)
    op.create_index("ix_news_articles_cat_subcat", "news_articles", ["category", "subcategory"], unique=False)
    op.create_index("ix_news_articles_original_category", "news_articles", ["original_source_category"], unique=False)

    # Archive legacy category in original_source_category
    op.execute("UPDATE news_articles SET original_source_category = category WHERE original_source_category IS NULL;")

    # Drop old check constraint and add new check constraint
    op.drop_constraint("ck_news_articles_valid_category", "news_articles", type_="check")

    # -------------------------------------------------------------------------
    # 5. Backfill historical articles to canonical categories & subcategories
    # -------------------------------------------------------------------------
    article_mappings = [
        # Art 1 -> Tech / Artificial Intelligence
        {"id": 1, "cat": "Tech", "cat_id": 1, "sub_code": "TECH_AI"},
        # Art 2 -> Entertainment / Gaming & Digital Entertainment
        {"id": 2, "cat": "Entertainment", "cat_id": 2, "sub_code": "ENT_GAMING"},
        # Art 3 -> Business & Finance / Personal Finance & Wealth Management
        {"id": 3, "cat": "Business & Finance", "cat_id": 3, "sub_code": "BIZ_PERSONAL_FINANCE"},
        # Art 4 -> Developments / Government & Public Policy
        {"id": 4, "cat": "Developments", "cat_id": 4, "sub_code": "DEV_GOV_POLICY"},
        # Art 5 -> Developments / Education & Learning Policy
        {"id": 5, "cat": "Developments", "cat_id": 4, "sub_code": "DEV_EDUCATION"},
        # Art 6 -> Developments / Education & Learning Policy
        {"id": 6, "cat": "Developments", "cat_id": 4, "sub_code": "DEV_EDUCATION"},
        # Art 7 -> Developments / Health & Medical Sciences
        {"id": 7, "cat": "Developments", "cat_id": 4, "sub_code": "DEV_HEALTH_MED"},
        # Art 8 -> Tech / Emerging Tech & Semiconductors
        {"id": 8, "cat": "Tech", "cat_id": 1, "sub_code": "TECH_EMERGING_HARDWARE"},
    ]

    for m in article_mappings:
        op.execute(
            sa.text(
                """
                UPDATE news_articles
                SET category = :cat,
                    category_id = :cat_id,
                    subcategory = (SELECT name FROM subcategories WHERE code = :sub_code),
                    subcategory_id = (SELECT id FROM subcategories WHERE code = :sub_code),
                    language = 'en'
                WHERE id = :art_id;
                """
            ).bindparams(
                cat=m["cat"],
                cat_id=m["cat_id"],
                sub_code=m["sub_code"],
                art_id=m["id"],
            )
        )

    # Re-apply new check constraint after backfill
    op.create_check_constraint(
        "ck_news_articles_valid_category",
        "news_articles",
        "category IN ('Entertainment', 'Sports', 'Tech', 'Developments', 'Business & Finance')",
    )

    # -------------------------------------------------------------------------
    # 6. Update google_document_records schema and historical rows
    # -------------------------------------------------------------------------
    op.add_column("google_document_records", sa.Column("subcategory", sa.String(length=100), nullable=True))
    op.add_column("google_document_records", sa.Column("google_drive_subcategory_folder_id", sa.String(length=255), nullable=True))
    op.create_index("ix_google_document_records_subcategory", "google_document_records", ["subcategory"], unique=False)

    for m in article_mappings:
        op.execute(
            sa.text(
                """
                UPDATE google_document_records
                SET category = :cat,
                    subcategory = (SELECT name FROM subcategories WHERE code = :sub_code)
                WHERE article_id = :art_id;
                """
            ).bindparams(
                cat=m["cat"],
                sub_code=m["sub_code"],
                art_id=m["id"],
            )
        )

    # -------------------------------------------------------------------------
    # 7. Update estd_duplicate_index schema and historical records
    # -------------------------------------------------------------------------
    op.add_column("estd_duplicate_index", sa.Column("subcategory", sa.String(length=100), nullable=True))
    op.create_index("ix_estd_duplicate_index_subcategory", "estd_duplicate_index", ["subcategory"], unique=False)

    for m in article_mappings:
        op.execute(
            sa.text(
                """
                UPDATE estd_duplicate_index
                SET category = :cat,
                    subcategory = (SELECT name FROM subcategories WHERE code = :sub_code)
                WHERE article_id = :art_id_str OR id = :art_id;
                """
            ).bindparams(
                cat=m["cat"],
                sub_code=m["sub_code"],
                art_id_str=str(m["id"]),
                art_id=m["id"],
            )
        )


def downgrade() -> None:
    # Remove indexes and columns added to duplicate index
    op.drop_index("ix_estd_duplicate_index_subcategory", "estd_duplicate_index")
    op.drop_column("estd_duplicate_index", "subcategory")

    # Remove columns added to google_document_records
    op.drop_index("ix_google_document_records_subcategory", "google_document_records")
    op.drop_column("google_document_records", "google_drive_subcategory_folder_id")
    op.drop_column("google_document_records", "subcategory")

    # Revert news_articles constraint and columns
    op.drop_constraint("ck_news_articles_valid_category", "news_articles", type_="check")
    op.drop_constraint("fk_news_articles_subcategory_id", "news_articles", type_="foreignkey")
    op.drop_index("ix_news_articles_original_category", "news_articles")
    op.drop_index("ix_news_articles_cat_subcat", "news_articles")
    op.drop_index("ix_news_articles_subcategory_id", "news_articles")
    op.drop_index("ix_news_articles_subcategory", "news_articles")
    op.drop_column("news_articles", "region")
    op.drop_column("news_articles", "language")
    op.drop_column("news_articles", "original_source_category")
    op.drop_column("news_articles", "subcategory_id")
    op.drop_column("news_articles", "subcategory")

    # Drop subcategories table
    op.drop_table("subcategories")

    # Revert categories columns
    op.drop_index("ix_categories_is_active", "categories")
    op.drop_index("ix_categories_code", "categories")
    op.drop_constraint("uq_categories_code", "categories", type_="unique")
    op.drop_column("categories", "updated_at")
    op.drop_column("categories", "is_active")
    op.drop_column("categories", "code")

    # Re-apply legacy check constraint
    op.create_check_constraint(
        "ck_news_articles_valid_category",
        "news_articles",
        "category IN ('Artificial Intelligence', 'Technology', 'Business', 'Education', 'Science')",
    )
