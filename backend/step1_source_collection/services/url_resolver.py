"""URL resolver service to un-shorten Google News redirects into real publisher URLs."""
import logging
import re
from typing import Dict, Optional
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger("estd.step1.url_resolver")

# In-memory cache for resolved URLs during pipeline execution
_RESOLVED_URL_CACHE: Dict[str, str] = {}


def is_google_news_redirect(url: str) -> bool:
    """Check if URL is a Google News tracking or redirect link."""
    if not url:
        return False
    lower = url.lower()
    return "news.google.com" in lower or "google.com/news" in lower


def resolve_real_publisher_url(url: str, timeout: float = 6.0) -> str:
    """Resolve a Google News redirect URL to the genuine publisher website URL.
    
    Args:
        url: The candidate URL (e.g. from Google News RSS).
        timeout: Network timeout in seconds.
        
    Returns:
        The canonical publisher destination URL, or the original URL on failure.
    """
    if not url or not is_google_news_redirect(url):
        return url

    # Check cache
    if url in _RESOLVED_URL_CACHE:
        return _RESOLVED_URL_CACHE[url]

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url, headers=headers)
            final_url = str(resp.url)

            # If redirected away from google.com, we found the real publisher URL
            if not is_google_news_redirect(final_url):
                _RESOLVED_URL_CACHE[url] = final_url
                logger.debug(f"Resolved Google News link to real publisher: {final_url}")
                return final_url

            # If still on google.com, check response HTML for canonical or meta refresh
            if resp.status_code == 200 and resp.text:
                soup = BeautifulSoup(resp.text[:10000], "html.parser")
                canonical = soup.find("link", rel="canonical")
                if canonical and canonical.get("href"):
                    cand = canonical["href"].strip()
                    if not is_google_news_redirect(cand):
                        _RESOLVED_URL_CACHE[url] = cand
                        return cand

                # Check for client-side JavaScript or meta redirect (e.g. url=...)
                meta_refresh = soup.find("meta", attrs={"http-equiv": re.compile(r"refresh", re.I)})
                if meta_refresh and meta_refresh.get("content"):
                    match = re.search(r"url=['\"]?([^'\"]+)['\"]?", meta_refresh["content"], re.I)
                    if match:
                        cand = match.group(1).strip()
                        if not is_google_news_redirect(cand):
                            _RESOLVED_URL_CACHE[url] = cand
                            return cand

    except Exception as exc:
        logger.debug(f"Could not resolve Google News URL '{url}': {exc}")

    # Fallback to original URL
    _RESOLVED_URL_CACHE[url] = url
    return url

