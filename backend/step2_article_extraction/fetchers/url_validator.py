"""URL validation and SSRF security protection for article scraping."""
import ipaddress
import socket
from urllib.parse import urlparse

from backend.step2_article_extraction.config import extraction_config
from backend.step2_article_extraction.exceptions.extraction_exceptions import (
    InvalidURLError,
    SSRFSecurityError,
)

FORBIDDEN_HOSTNAMES = {"localhost", "localhost.localdomain", "127.0.0.1", "0.0.0.0", "::1"}


class URLValidator:
    """Validates URLs for safety, scheme, structure, and SSRF prevention."""

    def __init__(self, allow_private_ips: bool = False):
        self.allow_private_ips = allow_private_ips

    def validate_url(self, url: str) -> str:
        """Validate URL format and ensure it does not violate SSRF constraints.

        Args:
            url: The string URL to validate.

        Returns:
            The validated and normalized URL string.

        Raises:
            InvalidURLError: If scheme or format is invalid.
            SSRFSecurityError: If host targets private or loopback networks.
        """
        if not url or not isinstance(url, str):
            raise InvalidURLError(str(url), "URL cannot be empty.")

        clean_url = url.strip()
        parsed = urlparse(clean_url)

        # Enforce HTTP / HTTPS schemes only
        if parsed.scheme.lower() not in ("http", "https"):
            raise InvalidURLError(
                clean_url,
                f"Unsupported scheme '{parsed.scheme}'. Only http and https are permitted.",
            )

        hostname = parsed.hostname
        if not hostname:
            raise InvalidURLError(clean_url, "URL has no hostname.")

        # SSRF checks
        if not self.allow_private_ips:
            lower_host = hostname.lower().strip()

            # Check known local hostnames
            if lower_host in FORBIDDEN_HOSTNAMES or lower_host.endswith(".local") or lower_host.endswith(".internal"):
                raise SSRFSecurityError(clean_url, lower_host)

            # Check if hostname is an IP address literal
            try:
                ip = ipaddress.ip_address(lower_host)
                if (
                    ip.is_private
                    or ip.is_loopback
                    or ip.is_link_local
                    or ip.is_reserved
                    or ip.is_multicast
                ):
                    raise SSRFSecurityError(clean_url, str(ip))
            except ValueError:
                # Hostname is a domain name, not an IP literal
                pass

        return clean_url
