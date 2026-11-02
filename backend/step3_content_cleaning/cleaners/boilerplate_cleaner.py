"""Conservative boilerplate cleaner module for stripping webpage noise."""
import re
from typing import List, Optional


class BoilerplateCleaner:
    """Removes non-article webpage noise such as advertisements, cookie notices, and social prompts."""

    # Standalone exact or prefix match patterns for obvious boilerplate lines/paragraphs
    _BOILERPLATE_LINE_PATTERNS = [
        # Advertisements
        re.compile(r"^\s*advertisement(\s*:.*|\s*[-–—].*|\s*$)", re.IGNORECASE),
        re.compile(r"^\s*sponsored\s+(content|post|story|stories|links?|by:?).*$", re.IGNORECASE),
        re.compile(r"^\s*promoted\s+(content|stories|post).*$", re.IGNORECASE),
        re.compile(r"^\s*ad\s*:\s*.*$", re.IGNORECASE),
        re.compile(r"^\s*\[\s*advertisement\s*\].*$", re.IGNORECASE),
        # Cookie and Privacy Banners
        re.compile(
            r"^\s*(we use cookies|this (website|site) uses cookies|by continuing to (use|browse) this site|"
            r"accept (all )?cookies|cookie (preferences|policy|settings)|manage cookies|"
            r"our website uses cookies|privacy and cookie policy).*",
            re.IGNORECASE,
        ),
        # Social Sharing & Follow Prompts
        re.compile(
            r"^\s*(share (this|on) (article|story|post|twitter|facebook|linkedin|reddit|whatsapp)|"
            r"follow (us )?on (twitter|x|facebook|instagram|linkedin|threads)|"
            r"share this:|follow @\w+|like us on facebook).*$",
            re.IGNORECASE,
        ),
        # Newsletter and Subscription Prompts
        re.compile(
            r"^\s*(sign up for (our )?(free )?[\w\s]{0,25}(newsletter|daily|weekly)|"
            r"subscribe to (our )?[\w\s]{0,25}(newsletter|daily updates?)|"
            r"get the latest (news|updates|headlines) delivered to your inbox|"
            r"enter your email( address)? to subscribe|"
            r"join our mailing list|subscribe now for (free|full access)|"
            r"stay updated with our newsletter).*$",
            re.IGNORECASE,
        ),
        # "Read more" / Related Story Links
        re.compile(
            r"^\s*((also )?read (more)?\s*:|related (articles?|stories|coverage|reading)\s*:|"
            r"recommended (reading|stories)\s*:|see also\s*:|click here to read more).*$",
            re.IGNORECASE,
        ),
        # Navigation & UI Fragments
        re.compile(r"^\s*(skip to (main )?content|back to top|menu|navigation)\s*$", re.IGNORECASE),
        re.compile(r"^\s*home\s*>\s*[\w\s]+\s*>\s*[\w\s]+.*$", re.IGNORECASE),
        # Footer & Copyright Boilerplate
        re.compile(
            r"^\s*((copyright|\xa9|\(c\))\s*(\d{4})?.*all rights reserved|"
            r"all rights reserved\.?|"
            r"terms of (service|use)\s*(\|\s*|\s*•\s*)privacy policy).*$",
            re.IGNORECASE,
        ),
        # Tracking / Code fragments
        re.compile(r"^\s*(googletag\.|window\._taboola|_gaq\.push|gtag\(|document\.write\().*$", re.IGNORECASE),
    ]

    def is_boilerplate(self, paragraph: str) -> bool:
        """Check if an isolated line or short paragraph is webpage boilerplate."""
        stripped = paragraph.strip()
        if not stripped:
            return True

        # High-confidence: If the line directly matches any boilerplate regex
        for pattern in self._BOILERPLATE_LINE_PATTERNS:
            if pattern.match(stripped):
                return True

        # Check for single-word / button leftovers
        lower_single = stripped.lower()
        if lower_single in {
            "subscribe",
            "share",
            "advertisement",
            "sponsored",
            "sign up",
            "read more",
            "continue reading",
            "listen to article",
        }:
            return True

        return False

    def remove_boilerplate(self, text: Optional[str]) -> str:
        """Filter out boilerplate lines while preserving all valid article paragraphs.

        Splits text by newline, checks each line/paragraph against conservative patterns,
        and reassembles the cleaned text.
        """
        if not text:
            return ""

        lines = text.split("\n")
        preserved_lines: List[str] = []

        for line in lines:
            stripped = line.strip()
            # Preserve empty lines as structural whitespace separators
            if not stripped:
                preserved_lines.append("")
                continue

            if self.is_boilerplate(stripped):
                continue

            preserved_lines.append(line)

        return "\n".join(preserved_lines)
