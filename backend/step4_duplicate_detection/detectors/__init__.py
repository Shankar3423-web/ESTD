"""Detectors package for Step 4 Duplicate Detection."""
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

__all__ = [
    "URLDetector",
    "ExactContentDetector",
    "SimilarityDetector",
    "SimilarityCandidate",
]
