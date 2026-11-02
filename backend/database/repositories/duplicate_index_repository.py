"""Repository for querying and persisting Step 4 duplicate index records."""
from typing import List, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from backend.common.logging.logger import logger
from backend.database.models.duplicate_index_record import DuplicateIndexRecord


class DuplicateIndexRepository:
    """Encapsulates database access for historical duplicate detection and indexing."""

    @staticmethod
    def find_by_normalized_url(
        session: Session,
        normalized_url: str,
    ) -> Optional[DuplicateIndexRecord]:
        """Find an existing index record matching the canonical normalized URL."""
        stmt = (
            select(DuplicateIndexRecord)
            .where(DuplicateIndexRecord.normalized_url == normalized_url)
            .order_by(DuplicateIndexRecord.is_duplicate.asc(), DuplicateIndexRecord.id.asc())
            .limit(1)
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def find_by_content_hash(
        session: Session,
        content_hash: str,
    ) -> Optional[DuplicateIndexRecord]:
        """Find an existing index record matching the SHA-256 content fingerprint."""
        stmt = (
            select(DuplicateIndexRecord)
            .where(DuplicateIndexRecord.content_hash == content_hash)
            .order_by(DuplicateIndexRecord.is_duplicate.asc(), DuplicateIndexRecord.id.asc())
            .limit(1)
        )
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_candidates_for_similarity(
        session: Session,
        category: Optional[str] = None,
        limit: int = 200,
        exclude_ids: Optional[List[int]] = None,
    ) -> List[DuplicateIndexRecord]:
        """Retrieve recent unique articles to serve as comparison candidates for TF-IDF similarity.
        
        Prioritizes articles within the same category to maximize relevance and minimize comparison cost.
        """
        stmt = select(DuplicateIndexRecord).where(DuplicateIndexRecord.is_duplicate.is_(False))

        if category:
            stmt = stmt.where(DuplicateIndexRecord.category == category)

        if exclude_ids:
            stmt = stmt.where(DuplicateIndexRecord.id.not_in(exclude_ids))

        # Order by newest first, limited to configured search horizon
        stmt = stmt.order_by(desc(DuplicateIndexRecord.created_at)).limit(limit)

        candidates = list(session.execute(stmt).scalars().all())
        
        # If category filtering yielded few candidates and category was specified, optionally retrieve cross-category recent articles
        if len(candidates) < min(10, limit) and category:
            fallback_stmt = (
                select(DuplicateIndexRecord)
                .where(DuplicateIndexRecord.is_duplicate.is_(False))
                .where(DuplicateIndexRecord.category != category)
            )
            if exclude_ids:
                fallback_stmt = fallback_stmt.where(DuplicateIndexRecord.id.not_in(exclude_ids))
            fallback_stmt = fallback_stmt.order_by(desc(DuplicateIndexRecord.created_at)).limit(limit - len(candidates))
            additional = list(session.execute(fallback_stmt).scalars().all())
            candidates.extend(additional)

        return candidates

    @staticmethod
    def save(
        session: Session,
        record: DuplicateIndexRecord,
    ) -> DuplicateIndexRecord:
        """Persist a single duplicate index record to the database."""
        session.add(record)
        session.flush()
        return record

    @staticmethod
    def save_batch(
        session: Session,
        records: List[DuplicateIndexRecord],
    ) -> List[DuplicateIndexRecord]:
        """Persist a batch of duplicate index records."""
        if not records:
            return []
        session.add_all(records)
        session.flush()
        return records

    @staticmethod
    def count_total(session: Session) -> int:
        """Count total records in the duplicate index."""
        stmt = select(func.count(DuplicateIndexRecord.id))
        return session.execute(stmt).scalar() or 0

    @staticmethod
    def count_unique(session: Session) -> int:
        """Count total unique articles in the duplicate index."""
        stmt = select(func.count(DuplicateIndexRecord.id)).where(DuplicateIndexRecord.is_duplicate.is_(False))
        return session.execute(stmt).scalar() or 0

    @staticmethod
    def count_duplicates(session: Session) -> int:
        """Count total duplicate articles recorded."""
        stmt = select(func.count(DuplicateIndexRecord.id)).where(DuplicateIndexRecord.is_duplicate.is_(True))
        return session.execute(stmt).scalar() or 0
