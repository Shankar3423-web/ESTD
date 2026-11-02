"""Metadata extractor for parsing article meta tags, OpenGraph, Twitter, and JSON-LD schemas."""
import json
import re
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup

from backend.common.utils.datetime_utils import normalize_datetime_to_iso


class MetadataExtractor:
    """Extracts article metadata such as title, author, publication date, canonical URL, and lead image."""

    def extract(self, soup: BeautifulSoup, original_url: str) -> Dict[str, Optional[str]]:
        """Extract metadata from parsed BeautifulSoup document.

        Args:
            soup: Parsed BeautifulSoup object of webpage.
            original_url: Fallback URL if canonical URL is not present.

        Returns:
            Dictionary with keys: title, author, published_at, canonical_url, image_url, source_name.
        """
        json_ld_data = self._extract_json_ld(soup)

        return {
            "title": self._extract_title(soup, json_ld_data),
            "author": self._extract_author(soup, json_ld_data),
            "published_at": self._extract_published_at(soup, json_ld_data),
            "canonical_url": self._extract_canonical_url(soup, json_ld_data, original_url),
            "image_url": self._extract_image_url(soup, json_ld_data),
            "source_name": self._extract_source_name(soup, json_ld_data),
        }

    def _extract_json_ld(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Parse schema.org JSON-LD scripts looking for NewsArticle/Article."""
        scripts = soup.find_all("script", type="application/ld+json")
        article_types = {
            "newsarticle",
            "article",
            "blogposting",
            "techarticle",
            "report",
            "scholarlyarticle",
            "liveblogposting",
        }

        for script in scripts:
            if not script.string:
                continue
            try:
                data = json.loads(script.string.strip())
                # Handle @graph wrapper
                items = data.get("@graph", [data]) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                for item in items:
                    if isinstance(item, dict):
                        type_val = item.get("@type", "")
                        types = [type_val] if isinstance(type_val, str) else (type_val if isinstance(type_val, list) else [])
                        for t in types:
                            if isinstance(t, str) and t.lower() in article_types:
                                return item
            except Exception:
                continue
        return {}

    def _extract_title(self, soup: BeautifulSoup, json_ld: Dict[str, Any]) -> Optional[str]:
        """Extract headline/title prioritizing og:title, json-ld headline, title tag, h1."""
        # 1. OpenGraph
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()
            if title:
                return title

        # 2. JSON-LD
        if json_ld.get("headline"):
            headline = str(json_ld["headline"]).strip()
            if headline:
                return headline

        # 3. Twitter
        tw_title = soup.find("meta", attrs={"name": "twitter:title"})
        if tw_title and tw_title.get("content"):
            title = tw_title["content"].strip()
            if title:
                return title

        # 4. <title> tag (clean off site name suffix if present)
        if soup.title and soup.title.string:
            title_text = soup.title.string.strip()
            # Split common site brand separators like " - Site" or " | Site"
            parts = re.split(r"\s+[|\-–—]\s+", title_text)
            if parts and parts[0].strip():
                return parts[0].strip()
            return title_text

        # 5. First <h1> tag
        h1 = soup.find("h1")
        if h1:
            h1_text = h1.get_text(strip=True)
            if h1_text:
                return h1_text

        return None

    def _extract_author(self, soup: BeautifulSoup, json_ld: Dict[str, Any]) -> Optional[str]:
        """Extract article author."""
        # 1. JSON-LD
        author_val = json_ld.get("author")
        if isinstance(author_val, dict) and author_val.get("name"):
            return str(author_val["name"]).strip()
        elif isinstance(author_val, list) and author_val:
            first = author_val[0]
            if isinstance(first, dict) and first.get("name"):
                return str(first["name"]).strip()
            elif isinstance(first, str):
                return first.strip()
        elif isinstance(author_val, str) and author_val.strip():
            return author_val.strip()

        # 2. Meta author tags
        for tag in [
            soup.find("meta", attrs={"name": "author"}),
            soup.find("meta", property="article:author"),
            soup.find("meta", property="og:author"),
        ]:
            if tag and tag.get("content"):
                auth_text = tag["content"].strip()
                if auth_text and not auth_text.startswith("http"):
                    return auth_text

        # 3. Rel author or common byline classes
        author_el = soup.find(attrs={"rel": "author"}) or soup.find(class_=re.compile(r"author[-_]name|byline[-_]author", re.IGNORECASE))
        if author_el:
            text = author_el.get_text(strip=True)
            if text and len(text) < 100:
                return text

        return None

    def _extract_published_at(self, soup: BeautifulSoup, json_ld: Dict[str, Any]) -> Optional[str]:
        """Extract and normalize publication timestamp to ISO 8601 UTC."""
        raw_dt: Optional[str] = None

        # 1. JSON-LD datePublished
        if json_ld.get("datePublished"):
            raw_dt = str(json_ld["datePublished"])

        # 2. Meta tags
        if not raw_dt:
            for tag in [
                soup.find("meta", property="article:published_time"),
                soup.find("meta", property="og:published_time"),
                soup.find("meta", attrs={"name": "publication_date"}),
                soup.find("meta", attrs={"name": "pubdate"}),
                soup.find("meta", attrs={"name": "date"}),
            ]:
                if tag and tag.get("content"):
                    raw_dt = tag["content"].strip()
                    break

        # 3. HTML5 <time> tag
        if not raw_dt:
            time_el = soup.find("time")
            if time_el:
                raw_dt = time_el.get("datetime") or time_el.get_text(strip=True)

        if raw_dt:
            return normalize_datetime_to_iso(raw_dt)

        return None

    def _extract_canonical_url(
        self,
        soup: BeautifulSoup,
        json_ld: Dict[str, Any],
        original_url: str,
    ) -> str:
        """Extract canonical URL or fallback to original URL."""
        # 1. Link rel=canonical
        canonical_link = soup.find("link", rel=lambda val: val and "canonical" in val.lower())
        if canonical_link and canonical_link.get("href"):
            href = canonical_link["href"].strip()
            if href.startswith("http://") or href.startswith("https://"):
                return href

        # 2. og:url
        og_url = soup.find("meta", property="og:url")
        if og_url and og_url.get("content"):
            url = og_url["content"].strip()
            if url.startswith("http://") or url.startswith("https://"):
                return url

        # 3. Fallback to original URL
        return original_url

    def _extract_image_url(self, soup: BeautifulSoup, json_ld: Dict[str, Any]) -> Optional[str]:
        """Extract lead article image URL."""
        # 1. og:image
        og_img = soup.find("meta", property="og:image")
        if og_img and og_img.get("content"):
            url = og_img["content"].strip()
            if url.startswith("http"):
                return url

        # 2. Twitter image
        tw_img = soup.find("meta", attrs={"name": "twitter:image"})
        if tw_img and tw_img.get("content"):
            url = tw_img["content"].strip()
            if url.startswith("http"):
                return url

        # 3. JSON-LD image
        img_val = json_ld.get("image")
        if isinstance(img_val, str) and img_val.startswith("http"):
            return img_val
        elif isinstance(img_val, dict) and img_val.get("url"):
            return str(img_val["url"])
        elif isinstance(img_val, list) and img_val and isinstance(img_val[0], str):
            return img_val[0]

        return None

    def _extract_source_name(self, soup: BeautifulSoup, json_ld: Dict[str, Any]) -> Optional[str]:
        """Extract publisher or site name."""
        og_site = soup.find("meta", property="og:site_name")
        if og_site and og_site.get("content"):
            return og_site["content"].strip()

        publisher = json_ld.get("publisher")
        if isinstance(publisher, dict) and publisher.get("name"):
            return str(publisher["name"]).strip()

        return None
