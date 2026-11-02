"""Unit tests for Step 8 category validation and mapping."""
import pytest

from backend.common.constants.categories import ESTDCategory
from backend.step8_gdrive_output.config.gdrive_settings import FINAL_CATEGORIES
from backend.step8_gdrive_output.exceptions import InvalidStep8CategoryError
from backend.step8_gdrive_output.validators.eligibility_validator import validate_category


class TestStep8CategoryValidation:
    """Test category validation against the 5 finalized ESTD categories."""

    def test_all_five_finalized_categories_accepted(self):
        """Verify each of the 5 canonical categories is valid."""
        expected = [
            "Entertainment",
            "Sports",
            "Tech",
            "Developments",
            "Business & Finance",
        ]
        assert list(FINAL_CATEGORIES) == expected

        for cat in expected:
            result = validate_category(cat)
            assert result == cat

    def test_enum_instances_accepted(self):
        """Verify ESTDCategory enum instances map correctly."""
        assert validate_category(ESTDCategory.ENTERTAINMENT) == "Entertainment"
        assert validate_category(ESTDCategory.SPORTS) == "Sports"
        assert validate_category(ESTDCategory.TECH) == "Tech"
        assert validate_category(ESTDCategory.DEVELOPMENTS) == "Developments"
        assert validate_category(ESTDCategory.BUSINESS_FINANCE) == "Business & Finance"

    def test_case_insensitive_matching(self):
        """Verify case-insensitive matching returns canonical capitalized form."""
        assert validate_category("entertainment") == "Entertainment"
        assert validate_category("SPORTS") == "Sports"
        assert validate_category("tech") == "Tech"
        assert validate_category("Developments") == "Developments"
        assert validate_category("business & finance") == "Business & Finance"

    def test_legacy_category_alias_mapping(self):
        """Verify legacy category names are resolved to canonical categories."""
        assert validate_category("Artificial Intelligence") == "Tech"
        assert validate_category("Technology") == "Tech"
        assert validate_category("Science") == "Developments"
        assert validate_category("Education") == "Developments"
        assert validate_category("Business") == "Business & Finance"

    def test_invalid_categories_rejected(self):
        """Verify non-supported categories raise InvalidStep8CategoryError."""
        invalid_categories = [
            "Cybersecurity News",
            "CYBERSECURITY NEWS",
            "NonExistentCategory",
            "UnknownTopic",
            "General",
            "",
            None,
        ]
        for inv in invalid_categories:
            with pytest.raises(InvalidStep8CategoryError) as exc_info:
                validate_category(inv)
            assert "Invalid category" in str(exc_info.value) or "Empty category" in str(exc_info.value)
