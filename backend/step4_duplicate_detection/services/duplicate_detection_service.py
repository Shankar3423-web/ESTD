"""Core orchestration service for Step 4 Duplicate Detection & Deduplication."""
from typing import Any, List, Optional
from sqlalchemy.orm import Session

from backend.common.logging.logger import logger
from backend.database.connection.session import get_db_session
from backend.database.models.duplicate_index_record import DuplicateIndexRecord
from backend.database.repositories.duplicate_index_repository import (
    DuplicateIndexRepository,
)
from backend.step3_content_cleaning.models.cleaned_article import CleanedArticle
from backend.step4_duplicate_detection.config import (
    DuplicateDetectionConfig,
    duplicate_config,
)
from backend.step4_duplicate_detection.detectors.exact_content_detector import (
    ExactContentDetector,
)
from backend.step4_duplicate_detection.detectors.similarity_detector import (
    SimilarityCandidate,
    SimilarityDetector,
)
from backend.step4_duplicate_detection.detectors.url_detector import (
    URLDetector,
)
from backend.step4_duplicate_detection.exceptions.duplicate_exceptions import (
    InvalidArticleForDeduplicationError,
)
from backend.step4_duplicate_detection.index.duplicate_index import (
    DuplicateIndex,
    EvaluatedBatchItem,
)
from backend.step4_duplicate_detection.models.duplicate_record import (
    DetectionScope,
    DuplicateDecision,
    DuplicateReason,
    DuplicateStatus,
)
from backend.step4_duplicate_detection.normalizers.text_normalizer import (
    normalize_content_for_hash,
)
from backend.step4_duplicate_detection.normalizers.url_normalizer import (
    normalize_url,
)
from backend.step4_duplicate_detection.schemas.duplicate_response import (
    DuplicateCheckResult,
)


class DuplicateDetectionService:
    """Production service for Step 4 duplicate detection across URL, content hash, and TF-IDF similarity."""

    def __init__(
        self,
        config: Optional[DuplicateDetectionConfig] = None,
        repository: Optional[DuplicateIndexRepository] = None,
        url_detector: Optional[URLDetector] = None,
        exact_detector: Optional[ExactContentDetector] = None,
        similarity_detector: Optional[SimilarityDetector] = None,
        index: Optional[DuplicateIndex] = None,
    ):
        self.config = config or duplicate_config
        self.repository = repository or DuplicateIndexRepository()
        self.url_detector = url_detector or URLDetector(repository=self.repository)
        self.exact_detector = exact_detector or ExactContentDetector(repository=self.repository)
        self.similarity_detector = similarity_detector or SimilarityDetector(
            threshold=self.config.similarity_threshold,
            ngram_range=(self.config.ngram_range_min, self.config.ngram_range_max),
            max_features=self.config.max_features,
            stop_words=self.config.stop_words,
        )
        self.index = index or DuplicateIndex(repository=self.repository)

    def check_article(
        self,
        article: CleanedArticle,
        session: Optional[Session] = None,
    ) -> DuplicateCheckResult:
        """Evaluate a single CleanedArticle through the 3-stage duplicate detection pipeline.
        
        Order of evaluation:
          1. URL Normalization & Matching
          2. SHA-256 Exact Content Fingerprint Matching
          3. TF-IDF Representation & Cosine Similarity Matching
          
        Args:
            article: CleanedArticle model produced by Step 3.
            session: Optional active SQLAlchemy database session.
            
        Returns:
            DuplicateCheckResult containing DuplicateDecision and the original CleanedArticle.
        """
        if not article:
            raise InvalidArticleForDeduplicationError(reason="Article payload cannot be None.")

        # If no external session provided, open a self-managed transactional session
        if session is None:
            try:
                with get_db_session() as managed_session:
                    return self._evaluate_article(article, managed_session)
            except Exception as exc:
                logger.warning(
                    f"Database session unavailable for historical deduplication: {exc}. "
                    "Proceeding with in-memory deduplication only."
                )
                return self._evaluate_article(article, session=None)

        return self._evaluate_article(article, session)

    def check_batch(
        self,
        articles: List[CleanedArticle],
        session: Optional[Session] = None,
    ) -> List[DuplicateCheckResult]:
        """Evaluate a batch of CleanedArticles with current-batch and historical deduplication.
        
        Args:
            articles: List of CleanedArticle models.
            session: Optional active SQLAlchemy database session.
            
        Returns:
            List of DuplicateCheckResult models corresponding 1-to-1 with input articles.
        """
        if not articles:
            return []

        # Reset batch in-memory cache for new batch run
        self.index.clear_batch()

        results: List[DuplicateCheckResult] = []

        if session is None:
            try:
                with get_db_session() as managed_session:
                    for article in articles:
                        result = self._evaluate_article(article, managed_session)
                        results.append(result)
                    return results
            except Exception as exc:
                logger.warning(
                    f"Database session unavailable for batch deduplication: {exc}. "
                    "Evaluating batch using in-memory detection only."
                )
                for article in articles:
                    result = self._evaluate_article(article, session=None)
                    results.append(result)
                return results

        for article in articles:
            result = self._evaluate_article(article, session)
            results.append(result)

        return results

    def _evaluate_article(
        self,
        article: CleanedArticle,
        session: Optional[Session],
    ) -> DuplicateCheckResult:
        """Internal worker executing the 3-stage detection pipeline for a single article."""
        # Step 0: URL & Content Extraction
        raw_url = article.canonical_url or article.url or ""
        normalized_url = normalize_url(raw_url)
        content_text = ""
        if article.cleaned_content is not None:
            content_text = article.cleaned_content
        elif article.content is not None:
            content_text = article.content
        elif article.description is not None:
            content_text = article.description
        content_hash = self.exact_detector.compute_content_hash(content_text)

        logger.debug(
            f"Evaluating article: '{article.title[:40]}...' | "
            f"normalized_url='{normalized_url}' | hash='{content_hash[:12]}...'"
        )

        # ---------------------------------------------------------------------
        # CHECK 1: URL MATCH (Cheapest & Deterministic)
        # ---------------------------------------------------------------------
        if self.config.enable_url_matching and normalized_url:
            url_match = self.url_detector.check_match(
                normalized_url=normalized_url,
                batch_cache=self.index.batch_url_cache,
                session=session,
                check_historical=self.config.enable_historical_detection,
            )
            if url_match is not None:
                scope, matched_item = url_match
                matched_id, matched_title, matched_url = self._extract_matched_metadata(matched_item)
                decision = DuplicateDecision.duplicate_by_url(
                    normalized_url=normalized_url,
                    content_hash=content_hash,
                    scope=scope,
                    matched_id=matched_id,
                    matched_title=matched_title,
                    matched_url=matched_url,
                )
                self._record_decision(article, decision, content_text, session)
                return DuplicateCheckResult(
                    status="duplicate",
                    decision=decision,
                    article=article,
                )

        # ---------------------------------------------------------------------
        # CHECK 2: EXACT CONTENT HASH (SHA-256)
        # ---------------------------------------------------------------------
        if self.config.enable_exact_content_matching and content_hash:
            hash_match = self.exact_detector.check_match(
                content_hash=content_hash,
                batch_cache=self.index.batch_hash_cache,
                session=session,
                check_historical=self.config.enable_historical_detection,
            )
            if hash_match is not None:
                scope, matched_item = hash_match
                matched_id, matched_title, matched_url = self._extract_matched_metadata(matched_item)
                decision = DuplicateDecision.duplicate_by_exact_content(
                    normalized_url=normalized_url,
                    content_hash=content_hash,
                    scope=scope,
                    matched_id=matched_id,
                    matched_title=matched_title,
                    matched_url=matched_url,
                )
                self._record_decision(article, decision, content_text, session)
                return DuplicateCheckResult(
                    status="duplicate",
                    decision=decision,
                    article=article,
                )

        # ---------------------------------------------------------------------
        # CHECK 3: TF-IDF + COSINE SIMILARITY
        # ---------------------------------------------------------------------
        computed_similarity_score: Optional[float] = None
        if self.config.enable_similarity_matching and len(content_text.strip()) >= 15:
            candidates = self.index.get_similarity_candidates(
                category=article.category,
                session=session,
                historical_limit=self.config.historical_candidate_limit,
                check_historical=self.config.enable_historical_detection,
            )
            if candidates:
                scope, best_candidate, similarity_score = self.similarity_detector.find_highest_similarity(
                    target_text=content_text,
                    candidates=candidates,
                    threshold=self.config.similarity_threshold,
                )
                computed_similarity_score = similarity_score
                if scope is not None and best_candidate is not None:
                    decision = DuplicateDecision.duplicate_by_similarity(
                        normalized_url=normalized_url,
                        content_hash=content_hash,
                        scope=scope,
                        similarity_score=similarity_score or 0.0,
                        matched_id=best_candidate.identifier,
                        matched_title=best_candidate.title,
                        matched_url=best_candidate.url,
                    )
                    self._record_decision(article, decision, content_text, session)
                    return DuplicateCheckResult(
                        status="duplicate",
                        decision=decision,
                        article=article,
                    )

        # ---------------------------------------------------------------------
        # FINAL DECISION: UNIQUE
        # ---------------------------------------------------------------------
        decision = DuplicateDecision.unique(
            normalized_url=normalized_url,
            content_hash=content_hash,
            similarity_score=computed_similarity_score,
        )
        self._record_decision(article, decision, content_text, session)

        logger.info(
            f"Article accepted as UNIQUE: '{article.title[:40]}...' "
            f"(category='{article.category}', max_similarity={computed_similarity_score})"
        )

        return DuplicateCheckResult(
            status="unique",
            decision=decision,
            article=article,
        )

    def _record_decision(
        self,
        article: CleanedArticle,
        decision: DuplicateDecision,
        content_text: str,
        session: Optional[Session],
    ) -> None:
        """Register the evaluation in the batch index and optionally persist to historical database."""
        # 1. Register in batch index
        self.index.register_item(
            article=article,
            normalized_url=decision.normalized_url,
            content_hash=decision.content_hash,
            is_duplicate=decision.is_duplicate,
            content=content_text,
            identifier=None,
            title=article.title,
            url=article.url,
            category=article.category,
            subcategory=getattr(article, "subcategory", None),
        )

        # 2. Database persistence
        if session is not None:
            should_persist = (
                (not decision.is_duplicate and self.config.persist_unique_articles)
                or (decision.is_duplicate and self.config.persist_duplicate_records)
            )
            if should_persist:
                try:
                    record = DuplicateIndexRecord(
                        title=article.title,
                        url=article.url,
                        normalized_url=decision.normalized_url,
                        content_hash=decision.content_hash,
                        category=article.category,
                        subcategory=getattr(article, "subcategory", None),
                        source_name=article.source_name,
                        source_type=article.source_type,
                        author=article.author,
                        published_at=article.published_at,
                        content_preview=content_text[:500] if content_text else None,
                        cleaned_content=content_text if not decision.is_duplicate else None,
                        is_duplicate=decision.is_duplicate,
                        duplicate_reason=decision.duplicate_reason.value if decision.duplicate_reason else None,
                        matched_record_id=int(decision.matched_article_id) if decision.matched_article_id and decision.matched_article_id.isdigit() else None,
                        similarity_score=decision.similarity_score,
                    )
                    self.repository.save(session, record)
                    session.commit()
                except Exception as exc:
                    session.rollback()
                    logger.error(f"Failed to persist duplicate index record for '{article.title}': {exc}")

    @staticmethod
    def _extract_matched_metadata(matched_item: Any) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract id, title, and url from either an EvaluatedBatchItem or a DuplicateIndexRecord."""
        matched_id: Optional[str] = None
        matched_title: Optional[str] = None
        matched_url: Optional[str] = None

        if isinstance(matched_item, DuplicateIndexRecord):
            matched_id = str(matched_item.id)
            matched_title = matched_item.title
            matched_url = matched_item.url
        elif isinstance(matched_item, EvaluatedBatchItem):
            matched_id = matched_item.identifier
            matched_title = matched_item.title
            matched_url = matched_item.url
        elif hasattr(matched_item, "title"):
            matched_title = getattr(matched_item, "title", None)
            matched_url = getattr(matched_item, "url", None)
            matched_id = str(getattr(matched_item, "id", None))

        return matched_id, matched_title, matched_url
