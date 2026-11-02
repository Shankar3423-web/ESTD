"""Exact content match detector using SHA-256 fingerprinting."""
import hashlib
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from backend.common.logging.logger import logger
from backend.database.models.duplicate_index_record import DuplicateIndexRecord
from backend.database.repositories.duplicate_index_repository import (
    DuplicateIndexRepository,
)
from backend.step4_duplicate_detection.models.duplicate_record import DetectionScope
from backend.step4_duplicate_detection.normalizers.text_normalizer import (
    normalize_content_for_hash,
)


class ExactContentDetector:
    """Detects duplicate articles by matching exact SHA-256 fingerprints of normalized body text."""

    def __init__(self, repository: Optional[DuplicateIndexRepository] = None):
        self.repository = repository or DuplicateIndexRepository()

    @staticmethod
    def compute_content_hash(content: Optional[str]) -> str:
        """Compute deterministic SHA-256 fingerprint from canonical normalized text.
        
        Args:
            content: Raw or cleaned article body text.
            
        Returns:
            64-character lowercase hex string of SHA-256 digest, or empty string if content is empty.
        """
        canonical_text = normalize_content_for_hash(content)
        if not canonical_text:
            return ""
        return hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()

    def check_match(
        self,
        content_hash: str,
        batch_cache: Dict[str, Any],
        session: Optional[Session] = None,
        check_historical: bool = True,
    ) -> Optional[Tuple[DetectionScope, Any]]:
        """Check whether the given content hash matches an existing article.
        
        Args:
            content_hash: SHA-256 hex digest of canonical article content.
            batch_cache: Dict mapping content_hash -> article/metadata from current batch.
            session: Optional active SQLAlchemy database session.
            check_historical: Whether to query historical database index.
            
        Returns:
            Tuple of (DetectionScope, matched_item) if duplicate detected, else None.
        """
        if not content_hash:
            return None

        # 1. In-batch check (in-memory)
        if content_hash in batch_cache:
            matched_item = batch_cache[content_hash]
            logger.info(f"Duplicate detected via BATCH EXACT CONTENT match: hash={content_hash[:12]}...")
            return DetectionScope.BATCH, matched_item

        # 2. Historical database check
        if check_historical and session is not None:
            historical_record: Optional[DuplicateIndexRecord] = self.repository.find_by_content_hash(
                session, content_hash
            )
            if historical_record is not None:
                logger.info(
                    f"Duplicate detected via HISTORICAL EXACT CONTENT match: hash={content_hash[:12]}... "
                    f"(Matched Record ID: {historical_record.id})"
                )
                return DetectionScope.HISTORICAL, historical_record

        return None
