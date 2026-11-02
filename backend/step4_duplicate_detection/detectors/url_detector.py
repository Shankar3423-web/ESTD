"""URL match detector for Step 4 Duplicate Detection."""
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from backend.common.logging.logger import logger
from backend.database.models.duplicate_index_record import DuplicateIndexRecord
from backend.database.repositories.duplicate_index_repository import (
    DuplicateIndexRepository,
)
from backend.step4_duplicate_detection.models.duplicate_record import DetectionScope


class URLDetector:
    """Detects duplicate articles by matching canonical normalized URLs.
    
    Checks in-memory batch cache first, then falls back to persistent database index.
    """

    def __init__(self, repository: Optional[DuplicateIndexRepository] = None):
        self.repository = repository or DuplicateIndexRepository()

    def check_match(
        self,
        normalized_url: str,
        batch_cache: Dict[str, Any],
        session: Optional[Session] = None,
        check_historical: bool = True,
    ) -> Optional[Tuple[DetectionScope, Any]]:
        """Check whether the given normalized URL matches an existing article.
        
        Args:
            normalized_url: Canonical normalized URL.
            batch_cache: Dict mapping normalized_url -> article/metadata from current batch.
            session: Optional active SQLAlchemy database session.
            check_historical: Whether to query historical database index.
            
        Returns:
            Tuple of (DetectionScope, matched_item) if duplicate detected, else None.
        """
        if not normalized_url:
            return None

        # 1. In-batch check (cheap, in-memory)
        if normalized_url in batch_cache:
            matched_item = batch_cache[normalized_url]
            logger.info(f"Duplicate detected via BATCH URL match: '{normalized_url}'")
            return DetectionScope.BATCH, matched_item

        # 2. Historical database check
        if check_historical and session is not None:
            historical_record: Optional[DuplicateIndexRecord] = self.repository.find_by_normalized_url(
                session, normalized_url
            )
            if historical_record is not None:
                logger.info(
                    f"Duplicate detected via HISTORICAL URL match: '{normalized_url}' "
                    f"(Matched Record ID: {historical_record.id})"
                )
                return DetectionScope.HISTORICAL, historical_record

        return None
