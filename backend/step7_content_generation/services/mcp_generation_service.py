"""MCP-First Content Generation Service connecting PostgreSQL MCP with Gemini AI."""
import time
from typing import Any, Dict, List, Optional

from backend.common.constants.categories import VALID_CATEGORIES
from backend.common.logging.logger import logger
from backend.step6_mcp.services.mcp_service import MCPService
from backend.step7_content_generation.exceptions import (
    ArticleIneligibleError,
    GenerationExecutionError,
    InsufficientSourceContentError,
)
from backend.step7_content_generation.schemas.generated_news import GeneratedNews
from backend.step7_content_generation.schemas.generation_request import (
    ArticleGenerationRequest,
    EligibleArticleSummary,
    GenerationResponse,
)
from backend.step7_content_generation.services.generation_service import (
    GenerationService,
)


class MCPGenerationService:
    """Service orchestrating knowledge-source article retrieval via MCP and Gemini AI synthesis."""

    def __init__(
        self,
        mcp_service: Optional[MCPService] = None,
        generation_service: Optional[GenerationService] = None,
    ):
        self.mcp_service = mcp_service or MCPService()
        self.generation_service = generation_service or GenerationService()
        # In-memory registry to avoid redundant duplicate generations during runtime
        self._generated_articles_cache: Dict[int, GeneratedNews] = {}

    def fetch_article_via_mcp(self, article_id: int) -> Dict[str, Any]:
        """Retrieve a specific article record from PostgreSQL through the Step 6 MCP query tool.

        Args:
            article_id: Primary key of news_articles record.

        Returns:
            Dictionary containing article row fields.

        Raises:
            ArticleIneligibleError: If article does not exist or MCP query fails.
        """
        # Validate ID parameter to ensure safe SQL
        if not isinstance(article_id, int) or article_id <= 0:
            raise ArticleIneligibleError(article_id, "Article ID must be a positive integer.")

        sql = f"""
        SELECT 
            id, 
            title, 
            description, 
            content, 
            url, 
            source_name, 
            source_type, 
            author, 
            published_at, 
            category,
            subcategory,
            language,
            region
        FROM news_articles 
        WHERE id = {article_id} 
        LIMIT 1;
        """
        logger.info(f"Querying ESTD knowledge source via MCP for article ID {article_id}...")
        try:
            results = self.mcp_service.query_knowledge_source(sql)
        except Exception as exc:
            logger.error(f"MCP query execution failed for article {article_id}: {exc}")
            raise GenerationExecutionError(f"Failed to query article via MCP: {exc}")

        if not results:
            raise ArticleIneligibleError(article_id, "Article not found in PostgreSQL knowledge source.")

        return results[0]

    def validate_article_eligibility(self, row: Dict[str, Any]) -> None:
        """Verify that an article satisfies all criteria required for AI news generation.

        Enforces the PART G Source Sufficiency Gate: rejects snippets, teasers, and empty text.

        Raises:
            InsufficientSourceContentError: If source content is a short snippet or teaser.
            ArticleIneligibleError: If content is missing, too short, or invalid category.
        """
        art_id = row.get("id", 0)
        title = row.get("title", "")
        content = row.get("content", "")
        category = row.get("category", "")
        url = row.get("url", "")

        if not title or not str(title).strip():
            raise ArticleIneligibleError(art_id, "Article title is empty.")

        clean_content = str(content).strip() if content else ""
        if not clean_content:
            raise ArticleIneligibleError(art_id, "Article content is missing or empty.")

        words = clean_content.split()
        if len(clean_content) < 200 or len(words) < 25:
            raise InsufficientSourceContentError(
                art_id,
                f"Source content is insufficient for publication generation "
                f"({len(clean_content)} chars < 200 min, {len(words)} words < 25 min). "
                f"Snippet or teaser detected.",
            )

        from backend.common.constants.categories import resolve_canonical_category
        resolved_cat = resolve_canonical_category(category)
        if not resolved_cat or resolved_cat not in VALID_CATEGORIES:
            raise ArticleIneligibleError(
                art_id,
                f"Article category '{category}' is invalid. Allowed: {list(VALID_CATEGORIES)}.",
            )

        if not url or not str(url).strip():
            raise ArticleIneligibleError(art_id, "Article source URL is missing.")

    def generate_from_mcp_article(
        self,
        request: ArticleGenerationRequest,
        force_regenerate: bool = False,
    ) -> GenerationResponse:
        """Full pipeline: Retrieve article via MCP -> Validate -> Generate via Gemini -> Validate output.

        Args:
            request: ArticleGenerationRequest containing article_id and optional guidance.
            force_regenerate: If True, bypass in-memory duplicate cache.

        Returns:
            GenerationResponse with structured GeneratedNews.
        """
        start_time = time.monotonic()
        art_id = request.article_id

        model_name = getattr(self.generation_service.settings, "gemini_model", "gemini-2.5-flash")
        if not isinstance(model_name, str):
            model_name = getattr(model_name, "_mock_name", "gemini-2.5-flash") or "gemini-2.5-flash"
        model_str = str(model_name)

        # Check duplicate generation cache
        if not force_regenerate and art_id in self._generated_articles_cache:
            cached = self._generated_articles_cache[art_id]
            logger.info(f"Returning cached generation for article ID {art_id} to prevent duplicate processing.")
            return GenerationResponse(
                success=True,
                article_id=art_id,
                data=cached,
                generation_time_ms=0.0,
                model_used=model_str,
            )

        # 1. Retrieve article through PostgreSQL MCP
        article_row = self.fetch_article_via_mcp(art_id)

        # 2. Check eligibility
        self.validate_article_eligibility(article_row)

        # 3. Call generation service
        generated = self.generation_service.generate_news(
            title=article_row["title"],
            content=article_row["content"],
            category=article_row["category"],
            source_name=article_row.get("source_name"),
            source_url=article_row["url"],
            author=article_row.get("author"),
            published_at=str(article_row.get("published_at")) if article_row.get("published_at") else None,
            description=article_row.get("description"),
            custom_instructions=request.custom_instructions,
            subcategory=article_row.get("subcategory"),
        )

        # 4. Cache generated result
        self._generated_articles_cache[art_id] = generated
        elapsed_ms = (time.monotonic() - start_time) * 1000

        model_name = getattr(self.generation_service.settings, "gemini_model", "gemini-2.5-flash")
        if not isinstance(model_name, str):
            model_name = getattr(model_name, "_mock_name", "gemini-2.5-flash") or "gemini-2.5-flash"

        return GenerationResponse(
            success=True,
            article_id=art_id,
            data=generated,
            generation_time_ms=round(elapsed_ms, 2),
            model_used=str(model_name),
        )

    def list_eligible_articles(
        self,
        limit: int = 50,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
    ) -> List[EligibleArticleSummary]:
        """Discover eligible articles in the PostgreSQL knowledge source via MCP."""
        limit_val = max(1, min(limit, 200))
        where_clauses = ["length(content) >= 50"]
        if category:
            from backend.common.constants.categories import resolve_canonical_category
            try:
                canonical_cat = resolve_canonical_category(category)
            except Exception:
                canonical_cat = category
            # SQL escape single quotes safely
            safe_cat = canonical_cat.replace("'", "''")
            where_clauses.append(f"category = '{safe_cat}'")

        if subcategory:
            safe_sub = subcategory.replace("'", "''")
            where_clauses.append(f"subcategory = '{safe_sub}'")

        where_sql = " AND ".join(where_clauses)
        sql = f"""
        SELECT 
            id, 
            title, 
            category, 
            subcategory,
            source_name, 
            length(content) as content_length, 
            published_at, 
            url 
        FROM news_articles 
        WHERE {where_sql}
        ORDER BY id ASC 
        LIMIT {limit_val};
        """
        logger.info(f"Listing eligible articles via MCP (limit={limit_val})...")
        results = self.mcp_service.query_knowledge_source(sql)
        summaries: List[EligibleArticleSummary] = []
        for r in results:
            summaries.append(
                EligibleArticleSummary(
                    id=r["id"],
                    title=r["title"],
                    category=r["category"],
                    subcategory=r.get("subcategory"),
                    source_name=r.get("source_name"),
                    content_length=r.get("content_length", 0),
                    published_at=str(r.get("published_at")) if r.get("published_at") else None,
                    url=r.get("url", ""),
                )
            )
        return summaries
