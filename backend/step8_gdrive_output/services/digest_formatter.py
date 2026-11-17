"""Digest formatter for compiling multi-article category digests for Google Drive export."""
from datetime import date, datetime, timezone
import json
import re
from typing import Any, Dict, List, Optional

from backend.database.models.news_article import NewsArticle


class DigestFormatter:
    """Formats a collection of approved news articles into a structured Google Document."""

    @staticmethod
    def build_document_title(category: str, digest_date: date) -> str:
        """Create a clean, standardized document title for Google Drive."""
        clean_cat = re.sub(r'[\\/:*?"<>|]', "-", category).strip()
        date_str = digest_date.strftime("%Y-%m-%d")
        return f"ESTD Daily Digest - {clean_cat} ({date_str})"

    @classmethod
    def format_category_digest(
        cls,
        category: str,
        digest_date: date,
        articles: List[NewsArticle],
    ) -> str:
        """Format a list of news articles into a unified daily digest document text."""
        date_display = digest_date.strftime("%B %d, %Y")
        story_count = len(articles)

        # Header block
        divider = "=" * 80
        thin_divider = "-" * 80

        lines = [
            divider,
            f"ESTD DAILY DIGEST: {category.upper()} EDITION",
            f"Date: {date_display} | Stories Included: {story_count} | Published by: ESTD Content Engine",
            divider,
            "",
            "EXECUTIVE BRIEFING & TODAY'S HEADLINES",
            thin_divider,
        ]

        if not articles:
            lines.extend([
                "No approved articles recorded for this category today.",
                "",
                divider,
            ])
            return "\n".join(lines)

        # 1. Quick Glance / Highlights
        for idx, art in enumerate(articles, 1):
            source_tag = f" ({art.source_name})" if art.source_name else ""
            summary_snippet = ""
            if art.description and art.description.strip():
                clean_desc = re.sub(r"\s+", " ", art.description.strip())
                summary_snippet = f" — {clean_desc[:160]}..." if len(clean_desc) > 160 else f" — {clean_desc}"
            lines.append(f"• [{idx}] {art.title}{source_tag}{summary_snippet}")

        lines.extend([
            "",
            "TABLE OF CONTENTS",
            thin_divider,
        ])

        # 2. Table of Contents
        for idx, art in enumerate(articles, 1):
            subcat = f" [{art.subcategory}]" if art.subcategory else ""
            lines.append(f"{idx}. {art.title}{subcat}")
            lines.append(f"   Source: {art.source_name or 'Wire Service'} | Slug: {art.slug or 'n/a'}")

        lines.extend([
            "",
            divider,
            "DETAILED STORIES & INTELLIGENCE WIRE",
            divider,
            "",
        ])

        # 3. Full Story Sections
        for idx, art in enumerate(articles, 1):
            subcat_str = art.subcategory or "General"
            pub_date_str = (
                art.source_published_at.strftime("%Y-%m-%d %H:%M UTC")
                if art.source_published_at
                else (art.published_at.strftime("%Y-%m-%d %H:%M UTC") if art.published_at else "Recent")
            )
            real_url = art.canonical_url or art.url or "N/A"

            # Parse entities
            entities_str = "None identified"
            if art.entities:
                if isinstance(art.entities, dict):
                    ent_parts = []
                    for k, v in art.entities.items():
                        if isinstance(v, list) and v:
                            ent_parts.append(f"{k}: {', '.join(str(item) for item in v[:5])}")
                    if ent_parts:
                        entities_str = "; ".join(ent_parts)
                elif isinstance(art.entities, list):
                    entities_str = ", ".join(str(e) for e in art.entities[:8])

            lines.extend([
                thin_divider,
                f"STORY {idx} OF {story_count}: {art.title.upper()}",
                thin_divider,
                f"• Category: {art.category} > {subcat_str}",
                f"• Publisher: {art.source_name or 'Unknown'}",
                f"• Real Source URL: {real_url}",
                f"• Published Date: {pub_date_str}",
                f"• SEO Slug: {art.slug or 'n/a'}",
                f"• Extracted Entities: {entities_str}",
                f"• Community Likes: {art.likes_count or 0}",
                "",
                "EXECUTIVE SUMMARY:",
                f"{art.description.strip() if art.description else 'No summary available.'}",
                "",
                "FULL STORY / AI SYNTHESIS:",
                f"{art.content.strip() if art.content else 'Full content unavailable.'}",
                "",
            ])

        # Footer
        lines.extend([
            divider,
            f"END OF ESTD DAILY DIGEST: {category.upper()} ({date_display})",
            "ESTD Multimedia Intelligence Platform — Automated Daily Editorial Archive",
            divider,
        ])

        return "\n".join(lines)

