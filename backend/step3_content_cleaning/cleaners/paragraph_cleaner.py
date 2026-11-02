"""Paragraph cleaner and conservative duplicate-paragraph removal module."""
import re
from typing import List, Optional, Set


class ParagraphCleaner:
    """Cleans paragraphs and removes exact duplicate extraction artifacts."""

    # Matches paragraphs that consist only of divider characters or decorative punctuation
    _DECORATIVE_ONLY_RE = re.compile(r"^[\s\-_=*#~•·—–|\^<>]+$")

    def __init__(self, deduplicate_repeated: bool = True):
        self.deduplicate_repeated = deduplicate_repeated

    def is_meaningful_paragraph(self, paragraph: str) -> bool:
        """Determine whether a paragraph contains meaningful textual content."""
        stripped = paragraph.strip()
        if not stripped:
            return False

        # Discard purely decorative divider lines or isolated symbols
        if self._DECORATIVE_ONLY_RE.match(stripped):
            return False

        # Discard stray punctuation-only paragraphs
        if len(stripped) <= 2 and not any(c.isalnum() for c in stripped):
            return False

        return True

    def clean_paragraphs(self, text: Optional[str]) -> str:
        """Clean individual paragraphs and remove repeated extraction artifacts.

        Preserves:
        - Headings
        - Lists and bullet items
        - Legitimate article text
        - Order of unique paragraphs
        """
        if not text:
            return ""

        # Normalize line endings first
        normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Split into candidate paragraphs by blank lines or multiple newlines
        raw_paragraphs = [p.strip() for p in re.split(r"\n\s*\n", normalized_text)]

        cleaned_paragraphs: List[str] = []
        seen_normalized: Set[str] = set()

        for para in raw_paragraphs:
            if not self.is_meaningful_paragraph(para):
                continue

            # Conservative exact repeated-paragraph removal
            if self.deduplicate_repeated:
                # Normalize key by collapsing internal whitespace and lowercasing
                normalized_key = re.sub(r"\s+", " ", para.strip().lower())
                if normalized_key in seen_normalized:
                    # Duplicate extraction noise, omit subsequent occurrence
                    continue
                seen_normalized.add(normalized_key)

            cleaned_paragraphs.append(para)

        return "\n\n".join(cleaned_paragraphs)
