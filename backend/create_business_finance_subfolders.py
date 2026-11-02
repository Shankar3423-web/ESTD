"""Create and verify all 6 Canonical Business & Finance Subcategory Folders in Google Drive.

Subcategories:
1. Financial Markets & Banking (BIZ_MARKETS, ID: 32)
2. Startups & Venture Capital (BIZ_STARTUPS, ID: 33)
3. Corporate Strategy & Earnings (BIZ_CORP_STRATEGY, ID: 34)
4. Personal Finance & Wealth Management (BIZ_PERSONAL_FINANCE, ID: 35)
5. Economy & Macroeconomics (BIZ_MACROECONOMY, ID: 36)
6. Trade, Supply Chain & Industry (BIZ_TRADE_INDUSTRY, ID: 37)
"""
import json
import sys
from pathlib import Path

# Setup paths
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.step8_gdrive_output.services.gdrive_service import GoogleDriveService

BUSINESS_FINANCE_ROOT_FOLDER_ID = "1832eaKMfMEq-wS27eLwpOxqvAW7ZzkLu"

BUSINESS_FINANCE_SUBCATEGORIES = [
    "Financial Markets & Banking",
    "Startups & Venture Capital",
    "Corporate Strategy & Earnings",
    "Personal Finance & Wealth Management",
    "Economy & Macroeconomics",
    "Trade, Supply Chain & Industry",
]


def main():
    print("=" * 80)
    print("ESTD - CREATE & VERIFY BUSINESS & FINANCE SUBCATEGORY FOLDERS IN GOOGLE DRIVE")
    print(f"Parent Business & Finance Folder ID: {BUSINESS_FINANCE_ROOT_FOLDER_ID}")
    print("=" * 80)

    gdrive_service = GoogleDriveService()

    # Verify parent folder metadata
    root_meta = gdrive_service.get_file_metadata(BUSINESS_FINANCE_ROOT_FOLDER_ID)
    print(f"Verified Parent: {root_meta.get('name')} (ID: {root_meta.get('id')}, Parents: {root_meta.get('parents')})\n")

    folder_map = {}
    for subcat in BUSINESS_FINANCE_SUBCATEGORIES:
        try:
            folder = gdrive_service.get_or_create_folder(
                name=subcat,
                parent_id=BUSINESS_FINANCE_ROOT_FOLDER_ID,
            )
            folder_map[subcat] = {
                "id": folder["id"],
                "name": folder.get("name", subcat),
                "parent_id": BUSINESS_FINANCE_ROOT_FOLDER_ID,
                "webViewLink": folder.get("webViewLink", f"https://drive.google.com/drive/folders/{folder['id']}"),
            }
            print(f" [VERIFIED/CREATED] {subcat:<40} -> ID: {folder['id']}")
        except Exception as exc:
            print(f" [FAILED]           {subcat:<40} -> Error: {exc}")

    print("\n" + "=" * 80)
    print("CANONICAL BUSINESS & FINANCE SUBCATEGORY FOLDERS SUMMARY:")
    print("=" * 80)
    for name, info in folder_map.items():
        print(f"\"{name}\": \"{info['id']}\",")
    print("=" * 80)
    print(f"Total Folders: {len(folder_map)} / {len(BUSINESS_FINANCE_SUBCATEGORIES)}")


if __name__ == "__main__":
    main()
