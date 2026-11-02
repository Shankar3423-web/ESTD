"""Safe Unicode normalizer for standardizing quotes, dashes, spaces, and encoding."""
from typing import Optional
import unicodedata


class UnicodeNormalizer:
    """Performs safe, non-destructive Unicode normalization."""

    # Map typographic quotes to standard ASCII equivalents
    _QUOTE_REPLACEMENTS = {
        "\u2018": "'",  # Left single quotation mark
        "\u2019": "'",  # Right single quotation mark / apostrophe
        "\u201a": "'",  # Single low-9 quotation mark
        "\u201b": "'",  # Single high-reversed-9 quotation mark
        "\u2032": "'",  # Prime
        "`": "'",       # Grave accent used as quote
        "\u00b4": "'",  # Acute accent used as quote
        "\u201c": '"',  # Left double quotation mark
        "\u201d": '"',  # Right double quotation mark
        "\u201e": '"',  # Double low-9 quotation mark
        "\u00ab": '"',  # Left-pointing double angle quotation mark
        "\u00bb": '"',  # Right-pointing double angle quotation mark
        "\u2033": '"',  # Double prime
    }

    # Map typographic dashes to standard hyphen-minus
    _DASH_REPLACEMENTS = {
        "\u2013": "-",  # En dash
        "\u2014": "-",  # Em dash
        "\u2015": "-",  # Horizontal bar
        "\u2012": "-",  # Figure dash
        "\u2212": "-",  # Minus sign
    }

    # Map exotic and non-breaking spaces to standard space
    _SPACE_REPLACEMENTS = {
        "\u00a0": " ",  # Non-breaking space
        "\u2000": " ",  # En quad
        "\u2001": " ",  # Em quad
        "\u2002": " ",  # En space
        "\u2003": " ",  # Em space
        "\u2004": " ",  # Three-per-em space
        "\u2005": " ",  # Four-per-em space
        "\u2006": " ",  # Six-per-em space
        "\u2007": " ",  # Figure space
        "\u2008": " ",  # Punctuation space
        "\u2009": " ",  # Thin space
        "\u200a": " ",  # Hair space
        "\u202f": " ",  # Narrow no-break space
        "\u205f": " ",  # Medium mathematical space
        "\u3000": " ",  # Ideographic space
    }

    # Invisible or formatting characters to strip safely
    _STRIP_CHARS = {
        "\u200b",  # Zero-width space
        "\ufeff",  # Zero-width non-breaking space (BOM)
        "\u200e",  # Left-to-right mark
        "\u200f",  # Right-to-left mark
        "\u00ad",  # Soft hyphen
    }

    # Typographic ellipsis
    _ELLIPSIS_REPLACEMENT = {
        "\u2026": "...",
    }

    def normalize(self, text: Optional[str]) -> str:
        """Safely normalize Unicode in text without destroying international characters.

        - Canonical NFC composition.
        - Standardizes curly/smart quotes to ASCII quotes.
        - Standardizes typographic dashes to standard dashes.
        - Converts non-breaking and exotic whitespace to standard ASCII space.
        - Strips zero-width and invisible control characters.
        - Fully preserves non-Latin, accented, and international characters.
        """
        if not text:
            return ""

        # Step 1: Canonical NFC composition
        normalized = unicodedata.normalize("NFC", text)

        # Step 2: Strip invisible/zero-width characters
        for char in self._STRIP_CHARS:
            if char in normalized:
                normalized = normalized.replace(char, "")

        # Step 3: Replace exotic spaces
        for char, replacement in self._SPACE_REPLACEMENTS.items():
            if char in normalized:
                normalized = normalized.replace(char, replacement)

        # Step 4: Replace quotes
        for char, replacement in self._QUOTE_REPLACEMENTS.items():
            if char in normalized:
                normalized = normalized.replace(char, replacement)

        # Step 5: Replace dashes
        for char, replacement in self._DASH_REPLACEMENTS.items():
            if char in normalized:
                normalized = normalized.replace(char, replacement)

        # Step 6: Replace ellipsis
        for char, replacement in self._ELLIPSIS_REPLACEMENT.items():
            if char in normalized:
                normalized = normalized.replace(char, replacement)

        return normalized
