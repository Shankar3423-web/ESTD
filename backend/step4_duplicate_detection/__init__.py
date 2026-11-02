"""Step 4 Duplicate Detection & Deduplication package for ESTD."""
from backend.step4_duplicate_detection.config import (
    DuplicateDetectionConfig,
    duplicate_config,
)
from backend.step4_duplicate_detection.models.duplicate_record import (
    DetectionScope,
    DuplicateDecision,
    DuplicateReason,
    DuplicateStatus,
)
from backend.step4_duplicate_detection.services.duplicate_detection_service import (
    DuplicateDetectionService,
)

__all__ = [
    "DuplicateDetectionService",
    "DuplicateDecision",
    "DuplicateStatus",
    "DuplicateReason",
    "DetectionScope",
    "DuplicateDetectionConfig",
    "duplicate_config",
]
