"""TF-IDF and Cosine Similarity detector for Step 4 Duplicate Detection."""
from typing import Any, List, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.common.logging.logger import logger
from backend.step4_duplicate_detection.config import duplicate_config
from backend.step4_duplicate_detection.exceptions.duplicate_exceptions import (
    SimilarityCalculationError,
)
from backend.step4_duplicate_detection.models.duplicate_record import DetectionScope


class SimilarityCandidate:
    """Represents a comparison candidate with associated text and origin scope."""

    def __init__(
        self,
        item: Any,
        text: str,
        scope: DetectionScope,
        identifier: Optional[str] = None,
        title: Optional[str] = None,
        url: Optional[str] = None,
    ):
        self.item = item
        self.text = text
        self.scope = scope
        self.identifier = identifier
        self.title = title
        self.url = url


class SimilarityDetector:
    """Calculates TF-IDF vector representations and evaluates cosine similarity against candidate articles."""

    def __init__(
        self,
        threshold: Optional[float] = None,
        ngram_range: Optional[Tuple[int, int]] = None,
        max_features: Optional[int] = None,
        stop_words: Optional[str] = "english",
    ):
        self.threshold = threshold if threshold is not None else duplicate_config.similarity_threshold
        self.ngram_range = (
            ngram_range
            if ngram_range is not None
            else (duplicate_config.ngram_range_min, duplicate_config.ngram_range_max)
        )
        self.max_features = max_features or duplicate_config.max_features
        self.stop_words = stop_words

    def create_vectorizer(self) -> TfidfVectorizer:
        """Instantiate a new scikit-learn TfidfVectorizer with configured parameters."""
        return TfidfVectorizer(
            ngram_range=self.ngram_range,
            max_features=self.max_features,
            stop_words=self.stop_words,
            lowercase=True,
            strip_accents="unicode",
        )

    def calculate_pairwise_similarity(self, text_a: str, text_b: str) -> float:
        """Compute cosine similarity score between two documents.
        
        Args:
            text_a: First article body text.
            text_b: Second article body text.
            
        Returns:
            Cosine similarity score as float between 0.0 and 1.0.
        """
        if not text_a or not text_b or not text_a.strip() or not text_b.strip():
            return 0.0

        try:
            vectorizer = self.create_vectorizer()
            tfidf_matrix = vectorizer.fit_transform([text_a, text_b])
            score = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
            # Bound numeric precision within [0.0, 1.0]
            return max(0.0, min(1.0, round(score, 4)))
        except ValueError as val_err:
            # Can occur if text consists entirely of stop words
            logger.debug(f"Pairwise similarity encountered empty vocabulary: {val_err}")
            return 0.0
        except Exception as exc:
            logger.error(f"Unexpected error in pairwise similarity calculation: {exc}")
            raise SimilarityCalculationError(str(exc)) from exc

    def find_highest_similarity(
        self,
        target_text: str,
        candidates: List[SimilarityCandidate],
        threshold: Optional[float] = None,
    ) -> Tuple[Optional[DetectionScope], Optional[SimilarityCandidate], Optional[float]]:
        """Compare target article text against all candidates and return highest match.
        
        Args:
            target_text: Target article body text.
            candidates: List of SimilarityCandidate objects from current batch and historical index.
            threshold: Optional threshold override. Defaults to self.threshold.
            
        Returns:
            Tuple of:
              - DetectionScope if score >= threshold, else None
              - Matched SimilarityCandidate if score >= threshold, else None
              - Highest computed similarity score (or None if no valid candidates)
        """
        effective_threshold = threshold if threshold is not None else self.threshold

        if not target_text or not target_text.strip() or not candidates:
            return None, None, None

        # Filter out empty candidate texts
        valid_candidates = [c for c in candidates if c.text and c.text.strip()]
        if not valid_candidates:
            return None, None, None

        try:
            corpus = [target_text] + [c.text for c in valid_candidates]
            vectorizer = self.create_vectorizer()
            tfidf_matrix = vectorizer.fit_transform(corpus)

            # Target is at index 0, candidates are at indices 1..N
            target_vec = tfidf_matrix[0:1]
            candidates_vec = tfidf_matrix[1:]

            similarities = cosine_similarity(target_vec, candidates_vec)[0]

            max_idx = int(np.argmax(similarities))
            max_score = float(similarities[max_idx])
            bounded_score = max(0.0, min(1.0, round(max_score, 4)))

            best_candidate = valid_candidates[max_idx]

            logger.debug(
                f"Top similarity candidate: '{best_candidate.title or best_candidate.identifier}' "
                f"score={bounded_score:.4f} (threshold={effective_threshold:.4f}, scope={best_candidate.scope})"
            )

            if bounded_score >= effective_threshold:
                logger.info(
                    f"Duplicate detected via {best_candidate.scope.value} SIMILARITY match: "
                    f"score={bounded_score:.4f} >= threshold={effective_threshold:.4f} "
                    f"(Matched: '{best_candidate.title or best_candidate.identifier}')"
                )
                return best_candidate.scope, best_candidate, bounded_score

            return None, None, bounded_score

        except ValueError as val_err:
            logger.debug(f"TF-IDF vectorizer found empty vocabulary: {val_err}")
            return None, None, 0.0
        except Exception as exc:
            logger.error(f"Error computing similarity across candidates: {exc}")
            raise SimilarityCalculationError(str(exc)) from exc
