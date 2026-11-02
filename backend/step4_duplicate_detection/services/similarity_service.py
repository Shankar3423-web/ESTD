"""Dedicated similarity service for TF-IDF and Cosine Similarity computations."""
from typing import List, Optional, Tuple

from backend.step4_duplicate_detection.detectors.similarity_detector import (
    SimilarityCandidate,
    SimilarityDetector,
)
from backend.step4_duplicate_detection.models.duplicate_record import DetectionScope


class SimilarityService:
    """Service wrapping TF-IDF vectorization and cosine similarity calculations."""

    def __init__(self, detector: Optional[SimilarityDetector] = None):
        self.detector = detector or SimilarityDetector()

    def calculate_pairwise_score(self, text_a: str, text_b: str) -> float:
        """Calculate pairwise cosine similarity between two texts."""
        return self.detector.calculate_pairwise_similarity(text_a, text_b)

    def evaluate_candidates(
        self,
        target_text: str,
        candidates: List[SimilarityCandidate],
        threshold: Optional[float] = None,
    ) -> Tuple[Optional[DetectionScope], Optional[SimilarityCandidate], Optional[float]]:
        """Evaluate target text against candidates and return match if threshold is exceeded."""
        return self.detector.find_highest_similarity(
            target_text=target_text,
            candidates=candidates,
            threshold=threshold,
        )
