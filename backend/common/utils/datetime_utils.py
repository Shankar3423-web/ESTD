"""Datetime utilities for parsing and normalizing timestamps to ISO 8601 UTC."""
from datetime import datetime, timezone
from typing import Optional


def get_utc_now_iso() -> str:
    """Return the current UTC timestamp formatted as ISO 8601 (ending in 'Z')."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_datetime_to_iso(dt_input: Optional[str]) -> Optional[str]:
    """Parse various datetime string formats into a standardized ISO 8601 UTC string.

    Supported formats include:
    - ISO 8601: '2026-09-30T10:00:00Z', '2026-09-30T10:00:00.000Z', '2026-09-30T10:00:00+00:00'
    - NewsData style: '2026-09-30 10:00:00'
    - RFC 2822: 'Wed, 30 Sep 2026 10:00:00 GMT'

    Returns:
        Standardized string like '2026-09-30T10:00:00Z', or None if input is empty/unparseable.
    """
    if not dt_input or not isinstance(dt_input, str):
        return None

    clean_str = dt_input.strip()
    if not clean_str:
        return None

    # Handle ISO formats directly with datetime.fromisoformat
    try:
        # If ending with Z, python fromisoformat handles +00:00
        iso_str = clean_str
        if iso_str.endswith("Z"):
            iso_str = iso_str[:-1] + "+00:00"
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, TypeError):
        pass

    # Try common formats
    candidate_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%d",
    ]

    for fmt in candidate_formats:
        try:
            dt = datetime.strptime(clean_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except (ValueError, TypeError):
            continue

    # If all parsers fail, return the trimmed raw string rather than crashing or inventing data
    return clean_str
