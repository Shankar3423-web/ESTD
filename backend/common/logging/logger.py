"""Structured and safe logging for ESTD backend."""
import logging
import re
import sys
from typing import Optional


class SensitiveDataFilter(logging.Filter):
    """Filter that scrubs potential API keys or query param secrets from log messages."""

    PATTERNS = [
        re.compile(r"(apikey=)[^&\s]+", re.IGNORECASE),
        re.compile(r"(token=)[^&\s]+", re.IGNORECASE),
        re.compile(r"(api_key=)[^&\s]+", re.IGNORECASE),
        re.compile(r"(key=)[^&\s]+", re.IGNORECASE),
        re.compile(r"(Bearer\s+)[^\s]+", re.IGNORECASE),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            msg = record.msg
            for pattern in self.PATTERNS:
                msg = pattern.sub(r"\1[REDACTED]", msg)
            record.msg = msg
        return True


def setup_logger(name: str = "estd") -> logging.Logger:
    """Set up and return a configured logger with secret redaction."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataFilter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger


logger = setup_logger("estd")


def log_request_start(provider: str, category: str, limit: Optional[int] = None) -> None:
    """Log the start of an external news provider request."""
    logger.info(f"[{provider.upper()}] Request started | category='{category}' | limit={limit}")


def log_request_success(
    provider: str,
    category: str,
    count: int,
    duration_ms: float,
    status_code: int = 200,
) -> None:
    """Log successful completion of an external news provider request."""
    logger.info(
        f"[{provider.upper()}] Request completed successfully | category='{category}' | "
        f"articles_received={count} | status_code={status_code} | duration={duration_ms:.2f}ms"
    )


def log_request_error(
    provider: str,
    category: str,
    error_message: str,
    status_code: Optional[int] = None,
) -> None:
    """Log failure of an external news provider request without exposing sensitive tokens."""
    status_part = f" | status_code={status_code}" if status_code else ""
    logger.error(
        f"[{provider.upper()}] Request failed | category='{category}'{status_part} | error='{error_message}'"
    )


def log_rss_fetch_start(source_name: str, category: str, url: str) -> None:
    """Log the start of an RSS feed fetch."""
    logger.info(f"[RSS] Fetching feed | source='{source_name}' | category='{category}' | url='{url}'")


def log_rss_fetch_success(
    source_name: str,
    category: str,
    entries_count: int,
    normalized_count: int,
    duplicates_removed: int,
    duration_ms: float,
) -> None:
    """Log successful completion of an RSS feed fetch and normalization."""
    logger.info(
        f"[RSS] Feed completed | source='{source_name}' | category='{category}' | "
        f"entries={entries_count} | normalized={normalized_count} | duplicates_removed={duplicates_removed} | "
        f"duration={duration_ms:.2f}ms"
    )


def log_rss_fetch_error(source_name: str, category: str, error_message: str) -> None:
    """Log failure of an RSS feed fetch."""
    logger.error(
        f"[RSS] Feed failed | source='{source_name}' | category='{category}' | error='{error_message}'"
    )

