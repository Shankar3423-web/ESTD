"""In-memory batch index and candidate coordinator for Step 4 Duplicate Detection."""
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.common.logging.logger import logger
from backend.database.models.duplicate_index_record import DuplicateIndexRecord
from backend.database.repositories.duplicate_index_repository import (
    DuplicateIndexRepository,
)
from backend.step4_duplicate_detection.detectors.similarity_detector import (
    SimilarityCandidate,
)
from backend.step4_duplicate_detection.models.duplicate_record import DetectionScope


class EvaluatedBatchItem:
    """Represents an evaluated article within the current processing batch."""

    def __init__(
        self,
        article: Any,
        normalized_url: str,
        content_hash: str,
        is_duplicate: bool,
        content: str,
        identifier: Optional[str] = None,
        title: Optional[str] = None,
        url: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
    ):
        self.article = article
        self.normalized_url = normalized_url
        self.content_hash = content_hash
        self.is_duplicate = is_duplicate
        self.content = content
        self.identifier = identifier
        self.title = title
        self.url = url
        self.category = category
        self.subcategory = subcategory


class DuplicateIndex:
    """Coordinates in-memory batch index state and persistent historical candidate retrieval."""

    def __init__(self, repository: Optional[DuplicateIndexRepository] = None):
        self.repository = repository or DuplicateIndexRepository()
        self._batch_by_url: Dict[str, EvaluatedBatchItem] = {}
        self._batch_by_hash: Dict[str, EvaluatedBatchItem] = {}
        self._batch_unique_items: List[EvaluatedBatchItem] = []

    def clear_batch(self) -> None:
        """Reset current-batch in-memory state."""
        self._batch_by_url.clear()
        self._batch_by_hash.clear()
        self._batch_unique_items.clear()

    @property
    def batch_url_cache(self) -> Dict[str, EvaluatedBatchItem]:
        """In-memory cache mapping normalized URLs to evaluated batch items."""
        return self._batch_by_url

    @property
    def batch_hash_cache(self) -> Dict[str, EvaluatedBatchItem]:
        """In-memory cache mapping content hashes to evaluated batch items."""
        return self._batch_by_hash

    def register_item(
        self,
        article: Any,
        normalized_url: str,
        content_hash: str,
        is_duplicate: bool,
        content: str,
        identifier: Optional[str] = None,
        title: Optional[str] = None,
        url: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
    ) -> EvaluatedBatchItem:
        """Register an evaluated article in the current batch index.
        
        Args:
            article: Source article object (e.g. CleanedArticle).
            normalized_url: Canonical normalized URL.
            content_hash: SHA-256 hex digest.
            is_duplicate: True if evaluated as duplicate.
            content: Normalized or cleaned content text.
            identifier: Optional ID string.
            title: Headline string.
            url: Raw URL string.
            category: Category string.
            subcategory: Subcategory string.
            
        Returns:
            The registered EvaluatedBatchItem.
        """
        item = EvaluatedBatchItem(
            article=article,
            normalized_url=normalized_url,
            content_hash=content_hash,
            is_duplicate=is_duplicate,
            content=content,
            identifier=identifier,
            title=title,
            url=url,
            category=category,
            subcategory=subcategory,
        )

        if normalized_url:
            self._batch_by_url[normalized_url] = item

        if content_hash:
            self._batch_by_hash[content_hash] = item

        if not is_duplicate:
            self._batch_unique_items.append(item)

        return item

    def get_similarity_candidates(
        self,
        category: Optional[str] = None,
        session: Optional[Session] = None,
        historical_limit: int = 200,
        check_historical: bool = True,
    ) -> List[SimilarityCandidate]:
        """Assemble comparison candidates from both in-memory batch and historical database index.
        
        Args:
            category: ESTD article category for focused candidate filtering.
            session: Optional active database session for historical queries.
            historical_limit: Max number of historical records to query.
            check_historical: Whether to include historical records.
            
        Returns:
            Combined list of SimilarityCandidate objects.
        """
        candidates: List[SimilarityCandidate] = []

        # 1. Batch Candidates (unique articles already accepted in this batch)
        for batch_item in self._batch_unique_items:
            if batch_item.content and batch_item.content.strip():
                candidates.append(
                    SimilarityCandidate(
                        item=batch_item,
                        text=batch_item.content,
                        scope=DetectionScope.BATCH,
                        identifier=batch_item.identifier,
                        title=batch_item.title,
                        url=batch_item.url,
                    )
                )

        # 2. Historical Candidates from database
        if check_historical and session is not None:
            historical_records: List[DuplicateIndexRecord] = self.repository.get_candidates_for_similarity(
                session=session,
                category=category,
                limit=historical_limit,
            )
            for record in historical_records:
                # Use cleaned_content or content_preview if available
                text = record.cleaned_content or record.content_preview or ""
                if text and text.strip():
                    candidates.append(
                        SimilarityCandidate(
                            item=record,
                            text=text,
                            scope=DetectionScope.HISTORICAL,
                            identifier=str(record.id),
                            title=record.title,
                            url=record.url,
                        )
                    )

        return candidates
