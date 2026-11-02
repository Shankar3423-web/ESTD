"""Unit tests for DriveFolderResolver idempotent hierarchy management."""
from unittest.mock import MagicMock
import pytest

from backend.step8_gdrive_output.config.gdrive_settings import FINAL_CATEGORIES, Step8Settings
from backend.step8_gdrive_output.exceptions import InvalidStep8CategoryError
from backend.step8_gdrive_output.services.folder_resolver import DriveFolderResolver
from backend.step8_gdrive_output.services.gdrive_service import GoogleDriveService


class TestDriveFolderResolver:
    """Test idempotent folder creation, discovery, and category resolution."""

    @pytest.fixture
    def mock_gdrive_service(self):
        """Mock GoogleDriveService storing folders in memory to simulate Google Drive."""
        service = MagicMock(spec=GoogleDriveService)
        storage = {}
        counter = {"id": 1}

        def fake_get_or_create(name: str, parent_id: str = None):
            key = (name, parent_id)
            if key not in storage:
                folder_id = f"folder_id_{counter['id']}"
                counter["id"] += 1
                storage[key] = {
                    "id": folder_id,
                    "name": name,
                    "parents": [parent_id] if parent_id else [],
                    "webViewLink": f"https://drive.google.com/drive/folders/{folder_id}",
                }
            return storage[key]

        service.get_or_create_folder.side_effect = fake_get_or_create
        service._storage = storage
        return service

    def test_idempotent_folder_initialization(self, mock_gdrive_service):
        """Verify initial run creates 1 root + 5 category folders; repeated runs reuse them."""
        resolver = DriveFolderResolver(gdrive_service=mock_gdrive_service)

        # Run 1: Create
        h1 = resolver.initialize_hierarchy()
        assert h1.is_fully_initialized is True
        assert h1.root_folder.name == "ESTD CONTENT"
        assert len(h1.category_folders) == 5

        for cat in FINAL_CATEGORIES:
            assert cat in h1.category_folders
            assert h1.category_folders[cat].parent_id == h1.root_folder.folder_id

        # Total folders created in simulated storage = 1 root + 5 categories = 6
        assert len(mock_gdrive_service._storage) == 6

        # Run 2: Re-initialize (simulate calling again)
        h2 = resolver.initialize_hierarchy(force_refresh=True)
        assert h2.root_folder.folder_id == h1.root_folder.folder_id
        for cat in FINAL_CATEGORIES:
            assert h2.category_folders[cat].folder_id == h1.category_folders[cat].folder_id

        # Total folders in storage must still be exactly 6 (NO duplicates created!)
        assert len(mock_gdrive_service._storage) == 6

        # Run 3: Without force_refresh (cache hit)
        h3 = resolver.initialize_hierarchy(force_refresh=False)
        assert h3.root_folder.folder_id == h1.root_folder.folder_id

    def test_resolve_category_folder_id(self, mock_gdrive_service):
        """Verify resolving category folder returns correct folder ID."""
        resolver = DriveFolderResolver(gdrive_service=mock_gdrive_service)

        ent_id = resolver.resolve_category_folder_id("Entertainment")
        sports_id = resolver.resolve_category_folder_id("Sports")
        tech_id = resolver.resolve_category_folder_id("Tech")
        dev_id = resolver.resolve_category_folder_id("Developments")
        biz_id = resolver.resolve_category_folder_id("Business & Finance")

        assert ent_id.startswith("folder_id_")
        assert sports_id.startswith("folder_id_")
        assert tech_id.startswith("folder_id_")
        assert dev_id.startswith("folder_id_")
        assert biz_id.startswith("folder_id_")
        # All IDs must be distinct
        assert len({ent_id, sports_id, tech_id, dev_id, biz_id}) == 5

        # Verify legacy category aliases map to canonical category folder
        assert resolver.resolve_category_folder_id("Artificial Intelligence") == tech_id
        assert resolver.resolve_category_folder_id("Technology") == tech_id
        assert resolver.resolve_category_folder_id("Science") == dev_id
        assert resolver.resolve_category_folder_id("Education") == dev_id
        assert resolver.resolve_category_folder_id("Business") == biz_id

    def test_resolve_invalid_category_raises(self, mock_gdrive_service):
        """Verify resolving an invalid category raises InvalidStep8CategoryError."""
        resolver = DriveFolderResolver(gdrive_service=mock_gdrive_service)
        with pytest.raises(InvalidStep8CategoryError):
            resolver.resolve_category_folder_id("Cybersecurity News")

    def test_initialize_sports_subcategories(self, mock_gdrive_service):
        """Verify initialize_category_subcategories proactively creates all 9 Sports subcategory folders."""
        resolver = DriveFolderResolver(gdrive_service=mock_gdrive_service)
        sports_subfolders = resolver.initialize_category_subcategories("Sports")

        expected_subcategories = [
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
        assert len(sports_subfolders) == 9
        for sub in expected_subcategories:
            assert sub in sports_subfolders
            assert sports_subfolders[sub].startswith("folder_id_")
