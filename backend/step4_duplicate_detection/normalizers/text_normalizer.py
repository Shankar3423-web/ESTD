"""Deterministic text normalization for exact content SHA-256 fingerprinting."""
import re
import unicodedata
from typing import Optional

_WHITESPACE_COLLAPSE_REGEX = re.compile(r"\s+")


def normalize_content_for_hash(text: Optional[str]) -> str:
    """Normalize article text into a canonical representation for SHA-256 fingerprinting.
    
    Processing steps:
      1. Handle None or non-string inputs safely (returns "").
      2. Apply Unicode NFC normalization.
      3. Convert text to lowercase for case-insensitive exact matching.
      4. Collapse all whitespace sequences (spaces, tabs, newlines) into single spaces.
      5. Strip surrounding leading and trailing whitespace.
      
    Args:
        text: Raw or cleaned article body text.
        
    Returns:
        Deterministic canonical string suitable for exact SHA-256 hashing.
    """
    if text is None:
        return ""

    if not isinstance(text, str):
        text = str(text)

    # Unicode canonical decomposition + composition
    normalized = unicodedata.normalize("NFC", text)

    # Lowercase conversion ensures casing variations do not produce different hashes
    normalized = normalized.lower()

    # Collapse all whitespace (newlines, tabs, spaces) into single spaces
    normalized = _WHITESPACE_COLLAPSE_REGEX.sub(" ", normalized)

    # Strip surrounding whitespace
    return normalized.strip()
