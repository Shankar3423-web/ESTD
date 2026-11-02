"""Whitespace normalizer for standardizing spaces, tabs, and line breaks."""
import re
from typing import Optional


class WhitespaceNormalizer:
    """Normalizes horizontal and vertical whitespace while preserving paragraph boundaries."""

    _HORIZONTAL_WS_RE = re.compile(r"[^\S\r\n]+")  # Whitespace except newlines
    _EXCESSIVE_NEWLINES_RE = re.compile(r"\n{3,}")

    def __init__(self, max_consecutive_blank_lines: int = 2):
        self.max_newlines = max_consecutive_blank_lines

    def normalize(self, text: Optional[str]) -> str:
        """Normalize spaces, tabs, and line endings.

        - Replaces carriage returns with standard newlines.
        - Converts tabs to spaces.
        - Collapses multiple consecutive spaces into a single space within lines.
        - Strips whitespace at the start and end of each line.
        - Collapses excessive blank lines to standard paragraph breaks (max 2 newlines).
        - Strips leading and trailing text whitespace.
        - Preserves paragraph structure without collapsing the text into one paragraph.
        """
        if not text:
            return ""

        # Step 1: Standardize line breaks
        standardized = text.replace("\r\n", "\n").replace("\r", "\n")

        # Step 2: Process line by line for horizontal whitespace and trimming
        lines = standardized.split("\n")
        cleaned_lines = []
        for line in lines:
            # Collapse internal horizontal whitespace
            cleaned_line = self._HORIZONTAL_WS_RE.sub(" ", line).strip()
            cleaned_lines.append(cleaned_line)

        reassembled = "\n".join(cleaned_lines)

        # Step 3: Collapse excessive blank lines (3 or more newlines -> 2 newlines)
        target_newlines = "\n" * self.max_newlines
        reassembled = self._EXCESSIVE_NEWLINES_RE.sub(target_newlines, reassembled)

        # Step 4: Final strip
        return reassembled.strip()
