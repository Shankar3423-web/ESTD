"""Deterministic URL normalization utility for Step 4 Duplicate Detection."""
import re
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from backend.common.logging.logger import logger

# Tracking parameters known to be marketing/analytics noise rather than content identity
TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "utm_reader",
    "utm_name",
    "fbclid",
    "gclid",
    "gclsrc",
    "dclid",
    "msclkid",
    "mc_eid",
    "yclid",
    "wbraid",
    "gbraid",
    "_ga",
    "_gl",
    "_hsenc",
    "_hsmi",
    "hsctatracking",
    "ref",
    "ref_src",
    "ref_url",
    "trk",
    "spm",
    "igshid",
}

# Regex for multiple consecutive forward slashes
_CONSECUTIVE_SLASHES_REGEX = re.compile(r"/+")


def normalize_url(url: Optional[str]) -> str:
    """Normalize a URL to its canonical form for deterministic duplicate matching.
    
    Processing steps:
      1. Strip surrounding whitespace.
      2. Lowercase scheme (defaults to 'https' if absent).
      3. Lowercase host and strip leading 'www.' prefix.
      4. Remove standard default ports (:80 for http, :443 for https).
      5. Normalize path (collapse consecutive slashes, remove trailing slash except root).
      6. Remove fragment (#section).
      7. Remove marketing/analytics tracking query parameters while strictly preserving
         content-identifying parameters.
      8. Sort remaining query parameters deterministically by key, then value.
      
    Args:
        url: Raw URL string.
        
    Returns:
        Canonical normalized URL string. Returns empty string if input is empty or invalid.
    """
    if not url or not isinstance(url, str):
        return ""

    raw_url = url.strip()
    if not raw_url:
        return ""

    try:
        # Prepend scheme if missing (e.g. "example.com/article" -> "https://example.com/article")
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw_url):
            raw_url = "https://" + raw_url

        split_result = urlsplit(raw_url)
        scheme = split_result.scheme.lower()
        if scheme not in ("http", "https"):
            scheme = "https"

        netloc = split_result.netloc.lower()
        
        # Split userinfo if any
        userinfo = ""
        if "@" in netloc:
            userinfo, netloc = netloc.split("@", 1)
            userinfo = userinfo + "@"

        # Split port if any
        hostname = netloc
        port = None
        if ":" in netloc:
            parts = netloc.split(":")
            hostname = parts[0]
            port = parts[1]

        # Strip www. prefix
        if hostname.startswith("www."):
            hostname = hostname[4:]

        # Strip default ports
        port_str = ""
        if port:
            if not ((scheme == "http" and port == "80") or (scheme == "https" and port == "443")):
                port_str = f":{port}"

        normalized_netloc = f"{userinfo}{hostname}{port_str}"

        # Normalize path
        path = split_result.path or "/"
        # Collapse consecutive slashes
        path = _CONSECUTIVE_SLASHES_REGEX.sub("/", path)
        # Strip trailing slash unless it's just "/"
        if len(path) > 1 and path.endswith("/"):
            path = path[:-1]

        # Filter and sort query parameters
        query = split_result.query
        normalized_query = ""
        if query:
            parsed_params = parse_qsl(query, keep_blank_values=True)
            filtered_params = [
                (k, v)
                for k, v in parsed_params
                if k.lower() not in TRACKING_PARAMS
            ]
            if filtered_params:
                # Sort alphabetically by key, then value for deterministic query string
                filtered_params.sort(key=lambda item: (item[0], item[1]))
                normalized_query = urlencode(filtered_params)

        # Drop fragment completely (split_result.fragment is ignored)
        normalized_url_str = urlunsplit((
            scheme,
            normalized_netloc,
            path,
            normalized_query,
            "",  # fragment is removed
        ))

        return normalized_url_str

    except Exception as exc:
        logger.warning(f"Error normalizing URL '{url}': {exc}. Returning sanitized fallback.")
        return raw_url.strip()
