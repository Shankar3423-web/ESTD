"""Audit and verification script for The Indian Express and The Hindu news ingestion."""
import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

sys.stdout.reconfigure(encoding="utf-8")

import feedparser
import httpx
from backend.step1_source_collection.rss.services.rss_service import RSSCollectionService
from backend.step1_source_collection.rss.sources.registry import get_source_registry
from backend.step2_article_extraction.services.extraction_service import ExtractionService
from backend.database.connection.session import get_db_session
from backend.database.models.news_article import NewsArticle
from backend.database.models.google_document_record import GoogleDocumentRecord


async def audit_sources():
    registry = get_source_registry()
    service = RSSCollectionService(registry=registry)
    extractor = ExtractionService()

    # Filter to Indian Express and The Hindu sources
    all_sources = registry.get_all_sources()
    ie_sources = [s for s in all_sources if "indian_express" in s.source_id.lower() or "indian express" in s.source_name.lower()]
    hindu_sources = [s for s in all_sources if "hindu" in s.source_id.lower() or "hindu" in s.source_name.lower()]

    print(f"Discovered {len(ie_sources)} Indian Express sources and {len(hindu_sources)} The Hindu sources in Registry.")

    audit_report: Dict[str, Any] = {
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "indian_express": {
            "configured_count": len(ie_sources),
            "sources": []
        },
        "the_hindu": {
            "configured_count": len(hindu_sources),
            "sources": []
        },
        "extraction_samples": [],
        "database_records": {
            "indian_express_count": 0,
            "the_hindu_count": 0,
            "items": []
        }
    }

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        # 1. Audit Indian Express Feeds
        for s in ie_sources:
            src_info = {
                "source_id": s.source_id,
                "source_name": s.source_name,
                "feed_url": s.feed_url,
                "category": s.category,
                "subcategory": s.subcategory,
                "enabled": s.enabled,
                "region": s.region,
                "language": s.language,
                "status": "UNKNOWN",
                "items_count": 0,
                "error": None,
                "sample_title": None,
                "sample_url": None,
                "sample_pubdate": None,
                "sample_has_image": False,
            }
            try:
                items = await service.collect_from_source(s, limit=5, client=client)
                src_info["status"] = "ACTIVE"
                src_info["items_count"] = len(items)
                if items:
                    sample = items[0]
                    src_info["sample_title"] = sample.title
                    src_info["sample_url"] = sample.url
                    src_info["sample_pubdate"] = str(sample.published_at) if sample.published_at else None
                    src_info["sample_has_image"] = bool(sample.image_url)
            except Exception as e:
                src_info["status"] = "ERROR"
                src_info["error"] = str(e)
            audit_report["indian_express"]["sources"].append(src_info)
            print(f"  [IE] {s.source_name:<35} | {src_info['status']} | items: {src_info['items_count']}")

        # 2. Audit The Hindu Feeds
        for s in hindu_sources:
            src_info = {
                "source_id": s.source_id,
                "source_name": s.source_name,
                "feed_url": s.feed_url,
                "category": s.category,
                "subcategory": s.subcategory,
                "enabled": s.enabled,
                "region": s.region,
                "language": s.language,
                "status": "UNKNOWN",
                "items_count": 0,
                "error": None,
                "sample_title": None,
                "sample_url": None,
                "sample_pubdate": None,
                "sample_has_image": False,
            }
            try:
                items = await service.collect_from_source(s, limit=5, client=client)
                src_info["status"] = "ACTIVE"
                src_info["items_count"] = len(items)
                if items:
                    sample = items[0]
                    src_info["sample_title"] = sample.title
                    src_info["sample_url"] = sample.url
                    src_info["sample_pubdate"] = str(sample.published_at) if sample.published_at else None
                    src_info["sample_has_image"] = bool(sample.image_url)
            except Exception as e:
                src_info["status"] = "ERROR"
                src_info["error"] = str(e)
            audit_report["the_hindu"]["sources"].append(src_info)
            print(f"  [TH] {s.source_name:<35} | {src_info['status']} | items: {src_info['items_count']}")

        # 3. Test extraction on a sample from each publisher
        test_samples = []
        ie_active = [s for s in audit_report["indian_express"]["sources"] if s["status"] == "ACTIVE" and s["sample_url"]]
        th_active = [s for s in audit_report["the_hindu"]["sources"] if s["status"] == "ACTIVE" and s["sample_url"]]

        if ie_active:
            test_samples.append(("The Indian Express", ie_active[0]))
        if th_active:
            test_samples.append(("The Hindu", th_active[0]))

        for pub_name, s_data in test_samples:
            sample_res = {
                "publisher": pub_name,
                "source_name": s_data["source_name"],
                "category": s_data["category"],
                "subcategory": s_data["subcategory"],
                "title": s_data["sample_title"],
                "url": s_data["sample_url"],
                "extraction_status": "UNKNOWN",
                "extracted_length": 0,
                "extracted_title": None,
                "error": None
            }
            try:
                from backend.step1_source_collection.models.news_item import NewsItem
                ni = NewsItem(
                    title=s_data["sample_title"] or "Sample Article",
                    url=s_data["sample_url"],
                    category=s_data["category"],
                    subcategory=s_data["subcategory"],
                    source_name=s_data["source_name"],
                    source_type="rss",
                    published_at=s_data["sample_pubdate"] or datetime.now(timezone.utc).isoformat()
                )
                ext_res = await extractor.extract_article(ni, force_fetch=True)
                sample_res["extraction_status"] = ext_res.extraction_status.value
                sample_res["extracted_length"] = len(ext_res.content or "")
                sample_res["extracted_title"] = ext_res.title
            except Exception as e:
                sample_res["extraction_status"] = "FAILED"
                sample_res["error"] = str(e)
            audit_report["extraction_samples"].append(sample_res)
            print(f"  [Extract] {pub_name:<20} | status: {sample_res['extraction_status']} | len: {sample_res['extracted_length']}")

    # 4. Check PostgreSQL database records
    with get_db_session() as s:
        db_arts = s.query(NewsArticle).filter(
            (NewsArticle.source_name.ilike("%Hindu%")) |
            (NewsArticle.source_name.ilike("%Indian Express%"))
        ).order_by(NewsArticle.id.asc()).all()

        for a in db_arts:
            gdoc = s.query(GoogleDocumentRecord).filter_by(article_id=a.id).first()
            audit_report["database_records"]["items"].append({
                "article_id": a.id,
                "title": a.title,
                "source_name": a.source_name,
                "category": a.category,
                "category_id": a.category_id,
                "subcategory": a.subcategory,
                "subcategory_id": a.subcategory_id,
                "url": a.url,
                "image_url": a.image_url,
                "published_at": a.published_at.isoformat() if a.published_at else None,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "has_content": bool(a.content and len(a.content) > 100),
                "content_chars": len(a.content or ""),
                "google_doc": {
                    "doc_id": gdoc.google_document_id if gdoc else None,
                    "doc_title": gdoc.document_title if gdoc else None,
                    "status": gdoc.status if gdoc else None,
                    "subfolder_id": gdoc.google_drive_subcategory_folder_id if gdoc else None,
                } if gdoc else None
            })
            if "Indian Express" in a.source_name:
                audit_report["database_records"]["indian_express_count"] += 1
            else:
                audit_report["database_records"]["the_hindu_count"] += 1

    out_path = project_root / "backend" / "audit_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2)

    print(f"\nAudit complete. Found {len(audit_report['database_records']['items'])} database records.")
    print(f"Results saved to {out_path}")

if __name__ == "__main__":
    asyncio.run(audit_sources())
