"""Unit tests for Step 4 URL, ExactContent, and Similarity detectors."""
import pytest
from unittest.mock import MagicMock

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
from backend.step4_duplicate_detection.models.duplicate_record import DetectionScope


class TestURLDetector:
    """Test suite for URL match detector."""

    def test_batch_url_match(self):
        detector = URLDetector()
        cache = {"https://example.com/news/1": {"id": 1, "title": "Article 1"}}
        result = detector.check_match("https://example.com/news/1", batch_cache=cache, check_historical=False)
        assert result is not None
        scope, item = result
        assert scope == DetectionScope.BATCH
        assert item["id"] == 1

    def test_historical_url_match(self):
        mock_repo = MagicMock()
        mock_record = MagicMock(id=42, title="Historical Article", url="https://example.com/news/1")
        mock_repo.find_by_normalized_url.return_value = mock_record

        detector = URLDetector(repository=mock_repo)
        mock_session = MagicMock()
        result = detector.check_match(
            "https://example.com/news/1",
            batch_cache={},
            session=mock_session,
            check_historical=True,
        )
        assert result is not None
        scope, record = result
        assert scope == DetectionScope.HISTORICAL
        assert record.id == 42

    def test_no_url_match_returns_none(self):
        detector = URLDetector()
        result = detector.check_match("https://example.com/brand-new", batch_cache={}, check_historical=False)
        assert result is None

    def test_empty_url_returns_none(self):
        detector = URLDetector()
        assert detector.check_match("", batch_cache={}) is None
        assert detector.check_match(None, batch_cache={}) is None


class TestExactContentDetector:
    """Test suite for SHA-256 exact content hash detector."""

    def test_deterministic_sha256_generation(self):
        detector = ExactContentDetector()
        text_a = "OpenAI released a new reasoning model for developers."
        text_b = "openai  released a   new reasoning model  for developers. "
        hash_a = detector.compute_content_hash(text_a)
        hash_b = detector.compute_content_hash(text_b)
        assert len(hash_a) == 64
        assert hash_a == hash_b

    def test_different_content_produces_different_hashes(self):
        detector = ExactContentDetector()
        hash_1 = detector.compute_content_hash("First article story.")
        hash_2 = detector.compute_content_hash("Completely different second story.")
        assert hash_1 != hash_2

    def test_empty_content_returns_empty_hash(self):
        detector = ExactContentDetector()
        assert detector.compute_content_hash("") == ""
        assert detector.compute_content_hash(None) == ""
        assert detector.compute_content_hash("   \n\t ") == ""

    def test_batch_content_hash_match(self):
        detector = ExactContentDetector()
        test_hash = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        cache = {test_hash: {"id": "item1", "title": "Batch Article"}}
        result = detector.check_match(test_hash, batch_cache=cache, check_historical=False)
        assert result is not None
        scope, item = result
        assert scope == DetectionScope.BATCH
        assert item["id"] == "item1"

    def test_historical_content_hash_match(self):
        mock_repo = MagicMock()
        mock_record = MagicMock(id=99, title="Historical Story")
        mock_repo.find_by_content_hash.return_value = mock_record

        detector = ExactContentDetector(repository=mock_repo)
        mock_session = MagicMock()
        test_hash = "9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba"
        result = detector.check_match(
            test_hash,
            batch_cache={},
            session=mock_session,
            check_historical=True,
        )
        assert result is not None
        scope, record = result
        assert scope == DetectionScope.HISTORICAL
        assert record.id == 99

    def test_no_hash_match_returns_none(self):
        detector = ExactContentDetector()
        assert detector.check_match("nonexistent_hash", batch_cache={}, check_historical=False) is None


class TestSimilarityDetector:
    """Test suite for TF-IDF vectorization and Cosine Similarity detector."""

    def test_pairwise_identical_text_similarity(self):
        detector = SimilarityDetector()
        text = "This is a detailed technological article about artificial intelligence advances in reasoning."
        score = detector.calculate_pairwise_similarity(text, text)
        assert score == 1.0

    def test_pairwise_completely_disjoint_text_similarity(self):
        detector = SimilarityDetector()
        text_a = "Quantum computing uses superposition and entanglement of qubits."
        text_b = "French bakery recipes require flour, yeast, butter, and precise fermentation time."
        score = detector.calculate_pairwise_similarity(text_a, text_b)
        assert score < 0.15

    def test_similarity_above_threshold_detects_duplicate(self):
        detector = SimilarityDetector(threshold=0.75)
        text_a = (
            "OpenAI announced a new reasoning model aimed at software developers today. "
            "The model demonstrates superior capabilities in solving mathematical benchmarks "
            "and generating complex code algorithms across multiple evaluation tasks."
        )
        text_b = (
            "OpenAI announced a new reasoning model aimed at software developers today. "
            "The model demonstrates superior capabilities in solving mathematical benchmarks "
            "and generating complex code algorithms."
        )
        candidates = [
            SimilarityCandidate(
                item={"id": "orig_1"},
                text=text_b,
                scope=DetectionScope.HISTORICAL,
                identifier="orig_1",
                title="OpenAI Dev Model",
            )
        ]
        scope, candidate, score = detector.find_highest_similarity(text_a, candidates, threshold=0.75)
        assert scope == DetectionScope.HISTORICAL
        assert candidate is not None
        assert candidate.identifier == "orig_1"
        assert score is not None
        assert score >= 0.75

    def test_similarity_below_threshold_returns_none(self):
        detector = SimilarityDetector(threshold=0.85)
        text_a = "Apple released a new smartphone model with titanium casing and improved battery life."
        text_b = "Samsung announced a new flagship phone featuring titanium frames and brighter displays."
        candidates = [
            SimilarityCandidate(
                item={"id": "phone_1"},
                text=text_b,
                scope=DetectionScope.BATCH,
                identifier="phone_1",
                title="Samsung Phone",
            )
        ]
        scope, candidate, score = detector.find_highest_similarity(text_a, candidates, threshold=0.85)
        assert scope is None
        assert candidate is None
        # Score is calculated but did not cross threshold
        assert score is not None
        assert score < 0.85

    def test_similarity_at_threshold_behavior(self):
        """Verify deterministic boundary behavior when similarity is exactly at threshold."""
        detector = SimilarityDetector()
        text = "Deep learning networks require vast amounts of compute and data."
        candidates = [
            SimilarityCandidate(
                item={"id": "exact_1"},
                text=text,
                scope=DetectionScope.BATCH,
                identifier="exact_1",
            )
        ]
        # Identical text produces score 1.0; setting threshold=1.0 must trigger match
        scope, candidate, score = detector.find_highest_similarity(text, candidates, threshold=1.0)
        assert scope == DetectionScope.BATCH
        assert candidate is not None
        assert score == 1.0

    def test_candidate_ranking_selects_highest_similarity(self):
        detector = SimilarityDetector(threshold=0.30)
        target = "Anthropic released Claude 3.5 Sonnet with improved coding capabilities."
        cand_low = SimilarityCandidate(
            item={"id": "low"},
            text="General technological news updates from various software providers.",
            scope=DetectionScope.BATCH,
            identifier="low",
        )
        cand_high = SimilarityCandidate(
            item={"id": "high"},
            text="Anthropic launched Claude 3.5 Sonnet featuring state of the art coding benchmarks.",
            scope=DetectionScope.HISTORICAL,
            identifier="high",
        )
        scope, best, score = detector.find_highest_similarity(target, [cand_low, cand_high], threshold=0.30)
        assert best is not None
        assert best.identifier == "high"
        assert scope == DetectionScope.HISTORICAL

    def test_empty_candidates_or_empty_target_returns_none(self):
        detector = SimilarityDetector()
        assert detector.find_highest_similarity("", []) == (None, None, None)
        assert detector.find_highest_similarity("Valid article text body.", []) == (None, None, None)
