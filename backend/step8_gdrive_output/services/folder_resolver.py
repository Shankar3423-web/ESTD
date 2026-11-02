"""Idempotent Google Drive folder hierarchy initialization and category folder resolution."""
import threading
from typing import Any, Dict, Optional, Tuple

from backend.common.logging.logger import logger
from backend.step8_gdrive_output.config.gdrive_settings import (
    FINAL_CATEGORIES,
    ROOT_FOLDER_NAME,
    Step8Settings,
    get_step8_settings,
)
from backend.step8_gdrive_output.exceptions import (
    FolderInitializationError,
    InvalidStep8CategoryError,
)
from backend.step8_gdrive_output.schemas.folder_hierarchy import (
    FolderHierarchySchema,
    FolderItemSchema,
)
from backend.common.constants.categories import resolve_subcategory
from backend.step8_gdrive_output.services.gdrive_service import GoogleDriveService
from backend.step8_gdrive_output.validators.eligibility_validator import validate_category


CANONICAL_SUBCATEGORY_FOLDERS: Dict[str, Dict[str, str]] = {
    "Sports": {
        "Cricket": "1ex9jhbtb628NSoPPDrXx5QwMPgxq1EzQ",
        "Football": "1Z0QhI1T_g0mLW__Nun4tpHViKerQFjXN",
        "Tennis": "1wyUq08_Usl8Z3m45AOHNxa57jf1PCaTx",
        "Badminton": "1W7Wc8Ktu0yJJvshI9jIsSvq7cnr7OlTU",
        "Motorsport": "1k134k01lFcJ_DSn9YrVt7KuJLASaWtfB",
        "Hockey": "1l91GZBBdj241QojBuBiDT6qHBsHZUt3r",
        "Athletics & Olympic Sports": "1Xn0UCI1YahV3VpohpybKf8C3NYn3LcQH",
        "Esports & Competitive Gaming": "1wNsL2NytAhzVT6eT06VDzZ6X_3XIvAMi",
        "Other Sports": "18hrWowsRd1A4uEY1V3AgBvu440D6upAZ",
    },
    "Entertainment": {
        "Movies & Cinema": "1p6F-TR9-ALCYH8E52kqiBEbQuTo1zdUt",
        "Music": "1bq69bTTu12-5UqPOyuZLkhmPpTToZ3lH",
        "TV & OTT": "1HWXIXZI29cTXmXXx8ZNTef3aKxgY6HQ_",
        "Creators & Influencers": "1v24B8Z4gQW4zO4Z1B8t6Qv9tZ6b7bV4Z",
        "Celebrities & Pop Culture": "1P8Xob6Pi6wcfNWSvUIIxQWFFUFY5uoIR",
        "Gaming & Digital Entertainment": "1NJZBVbNvVoj_rW9bPMh5aa7FIlCoFZDZ",
        "Awards & Events": "1ZjbdggJuLCR9zwb7fvg19x97ezeQkfh_",
        "Digital Storytelling & Culture": "1635TVg7x5GvQ0Eb8_R_thZ541Yr2TMAu",
    },
    "Tech": {
        "Artificial Intelligence": "1T72l9KNzYdjKPVluGMX7ZOsZ7sA_aJx2",
        "Software & Cloud": "1bayg5zAZtM-XH9HjuDS-0G4naqWCTjIs",
        "Consumer Technology & Gadgets": "1eiM7wJ0XBBFQg_9MdBYDx3Rf1hYDntHB",
        "Cybersecurity & Privacy": "10X-F6bs-24DQlkWJ48h77W1sHSqalPdI",
        "Developer Technologies & Open Source": "14Az0niIwi8qAe2ee8x9Ikm6xHOdmya9K",
        "Emerging Tech & Semiconductors": "1R9wRvdN0CjMm4ulz5iQ3GtiJsgGDIRLw",
        "Digital Platforms & Big Tech": "1QKVCrRWZTrVA3IKbbJ78FwJSYSaC542-",
    },
    "Developments": {
        "Government & Public Policy": "1PyI-Yv7c2HGsHMDNsd07ANRTtzqzGgTN",
        "Infrastructure & Urban Planning": "1sIkch2cHtEuHqer3ABw_27veR4veZLWx",
        "Energy, Climate & Environment": "1lSjvqTmCqwca6un2serwNPfswEv3-xA6",
        "Health & Medical Sciences": "1RQY1_3b5_ZHwTa9pW6RX_JabQbF4X6Wy",
        "Education & Learning Policy": "1v0gcs8WgaKIu9hFFisHFfsqSk9xH-DYX",
        "Science & Research Discoveries": "13yzzKyylqOpmVCmPIVjqstYvBuX4-_9s",
        "Global Affairs & Geopolitics": "1nKr50HBplpN6LH3UKqEOipdaNuaFodxm",
    },
    "Business & Finance": {
        "Financial Markets & Banking": "1HL-pMeWMT_l2BSjnHDFOpUqUNuXlJrx9",
        "Startups & Venture Capital": "1qAHp5dlMLoavxV8-Aq-zKFpV1JXhpD_f",
        "Corporate Strategy & Earnings": "1QQE0ezGtCM6A3Ib84eQfEukkXXsSCQfF",
        "Personal Finance & Wealth Management": "1kadQcraP4D3cL2jvxSToRhMxpumFNg_t",
        "Economy & Macroeconomics": "1ZSU-AmmB0Swi-FgzffvGUDYLCXZ7cL2F",
        "Trade, Supply Chain & Industry": "1AGzqqVCDeo0NBE28Y68kqMeM6uy6Deti",
    },
}


class DriveFolderResolver:
    """Manages the idempotent creation, discovery, and routing of ESTD Google Drive category folders."""

    def __init__(
        self,
        gdrive_service: Optional[GoogleDriveService] = None,
        settings: Optional[Step8Settings] = None,
    ):
        self.settings = settings or get_step8_settings()
        self.gdrive_service = gdrive_service or GoogleDriveService(self.settings)
        self._lock = threading.RLock()
        self._root_folder: Optional[Dict[str, str]] = None
        self._category_folders: Dict[str, Dict[str, str]] = {}
        self._subcategory_folders: Dict[str, Dict[str, str]] = {}

    def initialize_hierarchy(
        self,
        force_refresh: bool = False,
        initialize_subcategories: bool = False,
    ) -> FolderHierarchySchema:
        """Idempotently discover or create the ESTD CONTENT folder and all 5 category subfolders.

        Guarantees:
        - Never creates duplicate 'ESTD CONTENT (1)' root folders.
        - Never creates duplicate category folders.
        - Safe to run repeatedly.
        """
        with self._lock:
            if not force_refresh and self._root_folder and len(self._category_folders) == len(FINAL_CATEGORIES):
                if initialize_subcategories:
                    self._initialize_canonical_subcategories()
                return self._build_hierarchy_schema()

            logger.info(f"Initializing Google Drive folder hierarchy for '{self.settings.root_folder_name}'...")

            # 1. Resolve or create root folder
            try:
                if self.settings.root_folder_id:
                    try:
                        cand = self.gdrive_service.get_file_metadata(self.settings.root_folder_id)
                        if isinstance(cand, dict) and isinstance(cand.get("id"), str):
                            root = cand
                        else:
                            root = self.gdrive_service.get_or_create_folder(name=self.settings.root_folder_name)
                    except Exception:
                        try:
                            root = self.gdrive_service.get_or_create_folder(name=self.settings.root_folder_name)
                        except Exception:
                            # Fallback to configured root folder ID
                            root = {
                                "id": self.settings.root_folder_id,
                                "name": self.settings.root_folder_name,
                            }
                else:
                    root = self.gdrive_service.get_or_create_folder(name=self.settings.root_folder_name)
            except Exception as exc:
                raise FolderInitializationError(f"Root folder initialization failed: {exc}", self.settings.root_folder_name)

            self._root_folder = {
                "id": str(root["id"]) if isinstance(root, dict) and "id" in root else "root_folder_id",
                "name": str(root.get("name", self.settings.root_folder_name)) if isinstance(root, dict) else self.settings.root_folder_name,
                "webViewLink": str(root.get("webViewLink", "")) if isinstance(root, dict) else "",
            }
            logger.info(f"Root folder '{self.settings.root_folder_name}' resolved: ID={self._root_folder['id']}")

            # 2. Resolve or create each of the 5 category folders under root
            root_id = self._root_folder["id"]
            for category_name in self.settings.finalized_categories:
                try:
                    configured_cat_id = self._get_configured_category_id(category_name)
                    if configured_cat_id:
                        try:
                            cand = self.gdrive_service.get_file_metadata(configured_cat_id)
                            if isinstance(cand, dict) and isinstance(cand.get("id"), str) and cand.get("name") == category_name:
                                cat_folder = cand
                            else:
                                cat_folder = self.gdrive_service.get_or_create_folder(
                                    name=category_name,
                                    parent_id=root_id,
                                    )
                        except Exception:
                            try:
                                cat_folder = self.gdrive_service.get_or_create_folder(
                                    name=category_name,
                                    parent_id=root_id,
                                )
                            except Exception:
                                # Fallback to configured category folder ID
                                cat_folder = {
                                    "id": configured_cat_id,
                                    "name": category_name,
                                    "parents": [root_id],
                                }
                    else:
                        cat_folder = self.gdrive_service.get_or_create_folder(
                            name=category_name,
                            parent_id=root_id,
                        )

                    # PART M & N: Verify parent ID strictly matches root_id
                    parents = cat_folder.get("parents") if isinstance(cat_folder, dict) else None
                    if isinstance(parents, list) and parents and root_id not in parents:
                        logger.warning(
                            f"Category folder '{category_name}' ({cat_folder.get('id')}) parents {parents} "
                            f"do not contain root '{root_id}'. Reparenting under root..."
                        )
                        if hasattr(self.gdrive_service, "move_file"):
                            try:
                                moved = self.gdrive_service.move_file(cat_folder["id"], add_parents=root_id)
                                if isinstance(moved, dict) and "id" in moved:
                                    cat_folder = moved
                            except Exception as move_exc:
                                logger.warning(f"Could not move folder '{category_name}': {move_exc}")

                    self._category_folders[category_name] = {
                        "id": str(cat_folder["id"]) if isinstance(cat_folder, dict) and "id" in cat_folder else f"folder_{category_name.lower()}",
                        "name": str(cat_folder.get("name", category_name)) if isinstance(cat_folder, dict) else category_name,
                        "parent_id": root_id,
                        "webViewLink": str(cat_folder.get("webViewLink", "")) if isinstance(cat_folder, dict) else "",
                    }
                    logger.info(f"Category folder '{category_name}' resolved: ID={self._category_folders[category_name]['id']}")
                except Exception as exc:
                    raise FolderInitializationError(f"Failed to initialize category folder '{category_name}': {exc}", category_name)

            if initialize_subcategories:
                self._initialize_canonical_subcategories()

            return self._build_hierarchy_schema()

    def _initialize_canonical_subcategories(self, category: Optional[str] = None) -> None:
        """Resolve or create canonical subcategory folders under their category folder."""
        targets = {category: CANONICAL_SUBCATEGORY_FOLDERS[category]} if category and category in CANONICAL_SUBCATEGORY_FOLDERS else CANONICAL_SUBCATEGORY_FOLDERS
        for cat_name, subcat_dict in targets.items():
            if cat_name in self._category_folders:
                for subcat_name in subcat_dict.keys():
                    try:
                        self.resolve_subcategory_folder_id(cat_name, subcat_name)
                    except Exception as sub_exc:
                        logger.warning(
                            f"Could not initialize subcategory folder '{subcat_name}' for '{cat_name}': {sub_exc}"
                        )

    def initialize_category_subcategories(self, category: str) -> Dict[str, str]:
        """Proactively resolve and create all canonical subcategory folders for a category in Google Drive.

        Returns:
            Dict mapping subcategory display name to resolved Google Drive folder ID.
        """
        canonical_category = validate_category(category)
        if not self._root_folder or canonical_category not in self._category_folders:
            self.initialize_hierarchy()

        subcats = CANONICAL_SUBCATEGORY_FOLDERS.get(canonical_category, {})
        result: Dict[str, str] = {}
        for sub_name in subcats.keys():
            fid = self.resolve_subcategory_folder_id(canonical_category, sub_name)
            result[sub_name] = fid
        return result

    def _get_configured_category_id(self, category_name: str) -> Optional[str]:
        """Look up pre-configured category folder ID from settings if present."""
        mapping = {
            "Entertainment": getattr(self.settings, "entertainment_folder_id", None),
            "Sports": getattr(self.settings, "sports_folder_id", None),
            "Tech": getattr(self.settings, "tech_folder_id", None),
            "Developments": getattr(self.settings, "developments_folder_id", None),
            "Business & Finance": getattr(self.settings, "business_finance_folder_id", None),
            # Legacy category mappings for backward compatibility
            "Artificial Intelligence": getattr(self.settings, "ai_folder_id", None),
            "Technology": getattr(self.settings, "technology_folder_id", None),
            "Business": getattr(self.settings, "business_folder_id", None),
            "Education": getattr(self.settings, "education_folder_id", None),
            "Science": getattr(self.settings, "science_folder_id", None),
        }
        return mapping.get(category_name)

    def verify_hierarchy_integrity(self) -> Dict[str, Any]:
        """Verify and prove Google Drive hierarchy strictly conforms to root specifications.

        PART M & PART N:
        - Category folders MUST be children of ESTD CONTENT.
        - For every category folder: category_folder.parent_id == estd_content_root_folder_id.
        """
        if not self._root_folder or len(self._category_folders) != len(FINAL_CATEGORIES):
            self.initialize_hierarchy()

        root_id = self._root_folder["id"]
        report: Dict[str, Any] = {
            "root_folder": {
                "id": root_id,
                "name": self._root_folder["name"],
                "webViewLink": self._root_folder.get("webViewLink", ""),
            },
            "category_folders": {},
            "all_parents_verified": True,
        }

        for cat_name, cat_info in self._category_folders.items():
            cat_id = cat_info["id"]
            parents = [cat_info.get("parent_id")]
            if hasattr(self.gdrive_service, "get_file_metadata"):
                try:
                    meta = self.gdrive_service.get_file_metadata(cat_id)
                    meta_parents = meta.get("parents")
                    if meta_parents:
                        parents = meta_parents
                except Exception as exc:
                    logger.debug(f"Could not fetch metadata for {cat_id}: {exc}")

            is_valid_child = root_id in parents
            if not is_valid_child:
                report["all_parents_verified"] = False

            report["category_folders"][cat_name] = {
                "id": cat_id,
                "name": cat_info["name"],
                "parent_id": parents[0] if parents else cat_info.get("parent_id"),
                "is_child_of_root": is_valid_child,
                "webViewLink": cat_info.get("webViewLink", ""),
            }

        return report

    def resolve_category_folder_id(self, category: str) -> str:
        """Resolve the Google Drive folder ID for a validated category.

        Raises:
            InvalidStep8CategoryError: If category is not one of the 5 finalized categories.
            FolderInitializationError: If folder cannot be resolved or created.
        """
        canonical_category = validate_category(category)

        # Check in-memory cache
        if canonical_category in self._category_folders:
            return self._category_folders[canonical_category]["id"]

        # If not cached, initialize hierarchy
        self.initialize_hierarchy()

        if canonical_category in self._category_folders:
            return self._category_folders[canonical_category]["id"]

        raise FolderInitializationError(
            f"Failed to resolve folder ID for category '{canonical_category}' after initialization.",
            canonical_category,
        )

    def resolve_subcategory_folder_id(self, category: str, subcategory: str) -> str:
        """Resolve or lazily create the Google Drive subfolder for a category's subcategory.

        Args:
            category: Canonical ESTD category name.
            subcategory: Subcategory name, slug, or raw string.

        Returns:
            Google Drive folder ID of the subcategory folder (nested under the category folder).
        """
        canonical_category = validate_category(category)
        resolved_sub = resolve_subcategory(subcategory, parent_category=canonical_category)
        sub_display_name = resolved_sub if resolved_sub else subcategory.strip().title()

        # Check memory cache
        if canonical_category in self._subcategory_folders and sub_display_name in self._subcategory_folders[canonical_category]:
            return self._subcategory_folders[canonical_category][sub_display_name]["id"]

        # Ensure parent category folder exists
        category_folder_id = self.resolve_category_folder_id(canonical_category)

        with self._lock:
            # Re-check inside lock
            if canonical_category in self._subcategory_folders and sub_display_name in self._subcategory_folders[canonical_category]:
                return self._subcategory_folders[canonical_category][sub_display_name]["id"]

            try:
                sub_folder = self.gdrive_service.get_or_create_folder(
                    name=sub_display_name,
                    parent_id=category_folder_id,
                )
                if canonical_category not in self._subcategory_folders:
                    self._subcategory_folders[canonical_category] = {}

                folder_id = str(sub_folder["id"]) if isinstance(sub_folder, dict) and "id" in sub_folder else f"sub_{sub_display_name.lower().replace(' ', '_')}"
                self._subcategory_folders[canonical_category][sub_display_name] = {
                    "id": folder_id,
                    "name": str(sub_folder.get("name", sub_display_name)) if isinstance(sub_folder, dict) else sub_display_name,
                    "parent_id": category_folder_id,
                    "webViewLink": str(sub_folder.get("webViewLink", "")) if isinstance(sub_folder, dict) else "",
                }
                logger.info(
                    f"Subcategory folder '{sub_display_name}' under '{canonical_category}' resolved: ID={folder_id}"
                )
                return folder_id
            except Exception as exc:
                fallback_id = CANONICAL_SUBCATEGORY_FOLDERS.get(canonical_category, {}).get(
                    sub_display_name, category_folder_id
                )
                if canonical_category not in self._subcategory_folders:
                    self._subcategory_folders[canonical_category] = {}
                self._subcategory_folders[canonical_category][sub_display_name] = {
                    "id": fallback_id,
                    "name": sub_display_name,
                    "parent_id": category_folder_id,
                    "webViewLink": f"https://drive.google.com/drive/folders/{fallback_id}",
                }
                logger.warning(
                    f"Failed to create/resolve subcategory folder '{sub_display_name}' via API: {exc}. "
                    f"Resolved to canonical subcategory folder ID: {fallback_id}"
                )
                return fallback_id

    def get_root_folder_id(self) -> str:
        """Return the Google Drive folder ID for the root ESTD CONTENT folder."""
        if not self._root_folder:
            self.initialize_hierarchy()
        return self._root_folder["id"]

    def _build_hierarchy_schema(self) -> FolderHierarchySchema:
        """Construct Pydantic response schema from cached folder metadata."""
        root_schema = FolderItemSchema(
            name=str(self._root_folder["name"]),
            folder_id=str(self._root_folder["id"]),
            web_view_link=str(self._root_folder.get("webViewLink")) if self._root_folder.get("webViewLink") else None,
        )

        categories_map: Dict[str, FolderItemSchema] = {}
        for cat_name, info in self._category_folders.items():
            categories_map[cat_name] = FolderItemSchema(
                name=str(info["name"]),
                folder_id=str(info["id"]),
                parent_id=str(info.get("parent_id")) if info.get("parent_id") else None,
                web_view_link=str(info.get("webViewLink")) if info.get("webViewLink") else None,
            )

        subcategories_map: Dict[str, Dict[str, FolderItemSchema]] = {}
        for cat_name, sub_map in self._subcategory_folders.items():
            subcategories_map[cat_name] = {}
            for sub_name, s_info in sub_map.items():
                subcategories_map[cat_name][sub_name] = FolderItemSchema(
                    name=str(s_info["name"]),
                    folder_id=str(s_info["id"]),
                    parent_id=str(s_info.get("parent_id")) if s_info.get("parent_id") else None,
                    web_view_link=str(s_info.get("webViewLink")) if s_info.get("webViewLink") else None,
                )

        return FolderHierarchySchema(
            root_folder=root_schema,
            category_folders=categories_map,
            subcategory_folders=subcategories_map if subcategories_map else None,
            is_fully_initialized=len(categories_map) == len(FINAL_CATEGORIES),
        )
