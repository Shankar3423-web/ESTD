"""Content extractor for identifying and extracting the core article body from HTML."""
import copy
import re
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup, Tag

from backend.step2_article_extraction.exceptions.extraction_exceptions import (
    ContentExtractionError,
)

# Common noise element selectors to strip before evaluating text bodies
NOISE_TAGS = [
    "script",
    "style",
    "noscript",
    "nav",
    "header",
    "footer",
    "aside",
    "form",
    "button",
    "iframe",
    "svg",
    "canvas",
]

# Patterns in class or id indicating non-article noise
NOISE_CLASSES_PATTERN = re.compile(
    r"(comment|comments|sidebar|advert|ad-|ad_|promo|newsletter|cookie|popup|social|share|widget|menu|nav)",
    re.IGNORECASE,
)

# Patterns in class or id indicating potential article body containers
ARTICLE_CANDIDATE_PATTERN = re.compile(
    r"(article[-_]?body|story[-_]?body|story[-_]?content|entry[-_]?content|post[-_]?content|"
    r"article[-_]?content|main[-_]?content|article__body|article__content|rich[-_]?text|post[-_]?body)",
    re.IGNORECASE,
)


class ContentExtractor:
    """Extracts the main readable body text from an HTML document using structured and heuristic strategies."""

    def __init__(self, min_length: int = 80, min_words: int = 15):
        self.min_length = min_length
        self.min_words = min_words

    def extract(
        self,
        soup: BeautifulSoup,
        json_ld: Optional[Dict[str, Any]] = None,
        url: str = "",
    ) -> str:
        """Extract the main article body text.

        Args:
            soup: Parsed BeautifulSoup object.
            json_ld: Optional pre-parsed JSON-LD data.
            url: Page URL for contextual error reporting.

        Returns:
            Extracted text content of the article body.

        Raises:
            ContentExtractionError: If no readable article body can be extracted.
        """
        # Strategy 1: Check schema.org JSON-LD articleBody if available
        if json_ld and json_ld.get("articleBody"):
            ld_body = str(json_ld["articleBody"]).strip()
            if len(ld_body) >= self.min_length and len(ld_body.split()) >= self.min_words:
                return ld_body

        # Parse clean soup to safely strip noise without mutating metadata soup
        clean_soup = BeautifulSoup(str(soup), "html.parser")
        self._strip_noise(clean_soup)

        # Strategy 2: Look for semantic <article> element
        article_tag = clean_soup.find("article")
        if article_tag:
            body = self._extract_paragraphs_from_container(article_tag)
            if self._is_valid_body(body):
                return body

        # Strategy 3: Look for semantic <main> or [role="main"]
        main_tag = clean_soup.find("main") or clean_soup.find(attrs={"role": "main"})
        if main_tag:
            body = self._extract_paragraphs_from_container(main_tag)
            if self._is_valid_body(body):
                return body

        # Strategy 4: Candidate containers with matching class / id
        candidates = clean_soup.find_all(
            ["div", "section"],
            attrs={"class": ARTICLE_CANDIDATE_PATTERN},
        ) + clean_soup.find_all(
            ["div", "section"],
            attrs={"id": ARTICLE_CANDIDATE_PATTERN},
        )

        if candidates:
            best_candidate = self._score_candidates(candidates)
            if best_candidate:
                body = self._extract_paragraphs_from_container(best_candidate)
                if self._is_valid_body(body):
                    return body

        # Strategy 5: Paragraph clustering fallback across remaining body
        body_tag = clean_soup.find("body") or clean_soup
        paragraphs = body_tag.find_all("p")
        if paragraphs:
            valid_p_texts = []
            for p in paragraphs:
                p_text = p.get_text(strip=True)
                # Ignore very short paragraphs like copyright or date stamps unless in group
                if len(p_text.split()) >= 6:
                    valid_p_texts.append(p_text)

            combined_text = "\n\n".join(valid_p_texts)
            if self._is_valid_body(combined_text):
                return combined_text

        raise ContentExtractionError(
            url=url,
            reason="No readable article content or sustained paragraphs found in webpage.",
        )

    def _strip_noise(self, soup: BeautifulSoup) -> None:
        """Remove boilerplate elements, scripts, ads, and navigation from the soup."""
        for tag_name in NOISE_TAGS:
            for el in soup.find_all(tag_name):
                el.decompose()

        # Remove elements with strong noise classes/ids
        for el in soup.find_all(True):
            if not getattr(el, "attrs", None):
                continue
            classes = el.get("class") or []
            class_str = " ".join(classes) if isinstance(classes, list) else str(classes)
            id_str = str(el.get("id") or "")
            if NOISE_CLASSES_PATTERN.search(class_str) or NOISE_CLASSES_PATTERN.search(id_str):
                # Don't delete if it's the article or main container itself
                if el.name not in ["article", "main", "body", "html"]:
                    el.decompose()

    def _extract_paragraphs_from_container(self, container: Tag) -> str:
        """Extract text from all meaningful <p> tags within a container."""
        paragraphs = container.find_all("p")
        texts: List[str] = []

        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > 15:
                texts.append(text)

        if texts:
            return "\n\n".join(texts)

        # Fallback to direct container text if no <p> tags
        direct_text = container.get_text(separator="\n\n", strip=True)
        return direct_text

    def _score_candidates(self, candidates: List[Tag]) -> Optional[Tag]:
        """Score candidate containers based on paragraph count and text length."""
        best_tag: Optional[Tag] = None
        best_score = -1.0

        for candidate in candidates:
            paragraphs = candidate.find_all("p")
            text = candidate.get_text(strip=True)
            text_len = len(text)

            # Link density penalty
            links = candidate.find_all("a")
            link_text_len = sum(len(a.get_text(strip=True)) for a in links)
            link_density = (link_text_len / text_len) if text_len > 0 else 1.0

            # Ignore navigation menus or link-stuffed boxes
            if link_density > 0.5:
                continue

            score = len(paragraphs) * 50 + text_len * 0.1
            if score > best_score:
                best_score = score
                best_tag = candidate

        return best_tag

    def _is_valid_body(self, text: str) -> bool:
        """Check if extracted body meets minimal length and word requirements."""
        if not text:
            return False
        clean = text.strip()
        return len(clean) >= self.min_length and len(clean.split()) >= self.min_words
