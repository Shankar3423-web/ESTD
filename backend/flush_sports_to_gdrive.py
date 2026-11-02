"""Flush and upload all 21 staged Sports documents to Google Drive subcategory folders.

Executes Step 8 for all 21 Sports articles (9 subcategories, National & International)
after Google OAuth authentication is complete.
"""
import sys
import time
from pathlib import Path

# Setup paths
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.common.logging.logger import logger
from backend.database.connection.session import get_db_session
from backend.database.models.news_article import NewsArticle
from backend.database.models.google_document_record import GoogleDocumentRecord, DocumentStatus
from backend.step6_mcp.google.auth import (
    exchange_code_for_tokens,
    generate_authorization_url,
    refresh_access_token_if_needed,
)
from backend.step7_content_generation.schemas.generation_request import ArticleGenerationRequest
from backend.step7_content_generation.services.mcp_generation_service import MCPGenerationService
from backend.step8_gdrive_output.services.gdrive_service import GoogleDriveService
from backend.step8_gdrive_output.services.document_formatter import DocumentFormatter

SPORTS_FOLDER_ID = "1KbF5HuofvQaB7fYhaNFQESn2Xq_xBFLs"

SPORTS_SUBCATEGORIES = [
    "Cricket",
    "Football",
    "Tennis",
    "Badminton",
    "Motorsport",
    "Hockey",
    "Athletics & Olympic Sports",
    "Esports & Competitive Gaming",
    "Other Sports",
]


def check_live_api():
    """Verify live connectivity and authentication against Google Drive API."""
    try:
        gdrive_service = GoogleDriveService()
        meta = gdrive_service.get_file_metadata(SPORTS_FOLDER_ID)
        if isinstance(meta, dict) and meta.get("id") == SPORTS_FOLDER_ID:
            print(f"[OK] Google Drive API connection verified! Target Sports Folder: '{meta.get('name')}' ({SPORTS_FOLDER_ID})")
            return True
        return False
    except Exception as exc:
        return False


def main():
    print("=" * 80)
    print("ESTD SPORTS GOOGLE DRIVE FLUSH & UPLOAD PIPELINE")
    print("=" * 80)

    # Check for --code argument
    auth_code = None
    for i, arg in enumerate(sys.argv):
        if arg == "--code" and i + 1 < len(sys.argv):
            auth_code = sys.argv[i + 1]
            break
        elif arg.startswith("--code="):
            auth_code = arg.split("=", 1)[1]
            break

    if auth_code:
        print(f"\n[OAuth] Exchanging authorization code for fresh access & refresh tokens...")
        try:
            exchange_code_for_tokens(auth_code)
            print("[OAuth] SUCCESS! Fresh tokens obtained and saved to credentials files.")
        except Exception as exc:
            print(f"[OAuth] FAILED exchanging code: {exc}")
            sys.exit(1)

    # Check live Google Drive API
    if not check_live_api():
        auth_url = generate_authorization_url()
        print("\n" + "!" * 80)
        print("GOOGLE OAUTH AUTHENTICATION REQUIRED")
        print("!" * 80)
        print("Current credentials token has been expired or revoked by Google.")
        print("Google Drive rejected the connection with HTTP 401 UNAUTHENTICATED.")
        print("\nPlease follow these 2 steps to authorize:")
        print("1. Open this URL in your browser and authorize with shankar13052005@gmail.com:")
        print(f"\n   {auth_url}\n")
        print("2. Copy the 'code=' parameter from the redirected browser page address bar,")
        print("   and run this command:")
        print("   python flush_sports_to_gdrive.py --code <YOUR_AUTHORIZATION_CODE>")
        print("!" * 80)
        sys.exit(1)

    gdrive_service = GoogleDriveService()
    generation_service = MCPGenerationService()

    # Step 1: Ensure/Create all 9 Subcategory Folders under Sports
    print(f"\n[1/3] Resolving and creating subcategory folders under Sports ({SPORTS_FOLDER_ID})...")
    subfolder_map = {}
    for subcat in SPORTS_SUBCATEGORIES:
        try:
            folder = gdrive_service.get_or_create_folder(name=subcat, parent_id=SPORTS_FOLDER_ID)
            subfolder_map[subcat] = {
                "id": folder["id"],
                "webViewLink": folder.get("webViewLink", f"https://drive.google.com/drive/folders/{folder['id']}"),
            }
            print(f"  - Subcategory Folder '{subcat:30}': ID={folder['id']}")
        except Exception as exc:
            print(f"  - FAILED resolving folder for '{subcat}': {exc}")
            raise

    # Step 2: Fetch all 21 Sports articles from database
    print("\n[2/3] Fetching 21 Sports articles from PostgreSQL database...")
    with get_db_session() as session:
        articles = (
            session.query(NewsArticle)
            .filter(NewsArticle.category_id == 5)
            .order_by(NewsArticle.subcategory_id, NewsArticle.region)
            .all()
        )
        print(f"Found {len(articles)} Sports articles in database.")

        # Step 3: Generate, Format, and Upload each article to Google Drive
        print("\n[3/3] Uploading Google Documents to respective subcategory folders in Drive...")
        results = []

        for idx, art in enumerate(articles, 1):
            subcat_name = art.subcategory
            target_subfolder = subfolder_map.get(subcat_name, {}).get("id", SPORTS_FOLDER_ID)

            print(f"\n[{idx}/{len(articles)}] Processing Article {art.id}: '{art.title[:45]}...'")
            print(f"  Subcategory: {subcat_name} | Region: {art.region} | Target Folder: {target_subfolder}")

            # Check existing document record
            doc_rec = session.query(GoogleDocumentRecord).filter(GoogleDocumentRecord.article_id == art.id).first()
            if doc_rec and doc_rec.status == DocumentStatus.CREATED.value and doc_rec.google_document_id:
                print(f"  [ALREADY CREATED] Doc ID={doc_rec.google_document_id} | URL={doc_rec.google_document_url}")
                results.append({
                    "article_id": art.id,
                    "title": art.title,
                    "subcategory": subcat_name,
                    "region": art.region,
                    "doc_id": doc_rec.google_document_id,
                    "doc_url": doc_rec.google_document_url,
                    "status": "EXISTS",
                })
                continue

            # Generate via Step 7 Gemini
            try:
                gen_req = ArticleGenerationRequest(article_id=art.id)
                gen_resp = generation_service.generate_from_mcp_article(gen_req)
                if not gen_resp.success or not gen_resp.data:
                    raise RuntimeError(f"Step 7 generation failed: {gen_resp.message}")
                gen_news = gen_resp.data

                # Format Google Document content
                doc_title = DocumentFormatter.sanitize_title(gen_news.title, article_id=art.id)
                formatted_body = DocumentFormatter.format_document_content(
                    news=gen_news,
                    article_id=art.id,
                    original_published_at=str(art.published_at) if art.published_at else None,
                )

                # Upload to Google Drive via API
                uploaded = gdrive_service.create_google_document(
                    title=doc_title,
                    content=formatted_body,
                    folder_id=target_subfolder,
                )

                doc_id = uploaded["id"]
                doc_url = uploaded.get("webViewLink", f"https://docs.google.com/document/d/{doc_id}/edit")

                # Update database record
                if not doc_rec:
                    doc_rec = GoogleDocumentRecord(
                        article_id=art.id,
                        document_title=doc_title,
                        category="Sports",
                        subcategory=subcat_name,
                        google_drive_root_folder_id="1RjdnF8JcwGp-OyNipwM20Gg8XrcQJEk8",
                        google_drive_category_folder_id=SPORTS_FOLDER_ID,
                        google_drive_subcategory_folder_id=target_subfolder,
                        status=DocumentStatus.CREATED.value,
                        google_document_id=doc_id,
                        google_document_url=doc_url,
                    )
                    session.add(doc_rec)
                else:
                    doc_rec.document_title = doc_title
                    doc_rec.status = DocumentStatus.CREATED.value
                    doc_rec.google_document_id = doc_id
                    doc_rec.google_document_url = doc_url
                    doc_rec.google_drive_category_folder_id = SPORTS_FOLDER_ID
                    doc_rec.google_drive_subcategory_folder_id = target_subfolder
                    doc_rec.subcategory = subcat_name
                    doc_rec.last_error = None

                session.commit()
                print(f"  [SUCCESS] Google Doc Created: ID={doc_id} | URL={doc_url}")
                results.append({
                    "article_id": art.id,
                    "title": doc_title,
                    "subcategory": subcat_name,
                    "region": art.region,
                    "doc_id": doc_id,
                    "doc_url": doc_url,
                    "status": "CREATED",
                })
            except Exception as exc:
                print(f"  [ERROR] Upload failed for article {art.id}: {exc}")
                if doc_rec:
                    doc_rec.status = DocumentStatus.FAILED.value
                    doc_rec.last_error = str(exc)
                    session.commit()
                results.append({
                    "article_id": art.id,
                    "title": art.title,
                    "subcategory": subcat_name,
                    "region": art.region,
                    "doc_id": None,
                    "doc_url": None,
                    "status": f"FAILED: {exc}",
                })

    print("\n" + "=" * 80)
    print("FINAL SUMMARY: SPORTS GOOGLE DRIVE DOCUMENTS")
    print("=" * 80)
    for r in results:
        print(f"Article {r['article_id']:4d} | {r['subcategory']:28} | {r['region'] or 'none':13} | {r['status']:7} | {r.get('doc_url')}")
    print("=" * 80)


if __name__ == "__main__":
    main()
