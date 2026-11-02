"""Configuration settings for Step 3 Content Cleaning & Normalization."""
from pydantic_settings import BaseSettings


class CleaningConfig(BaseSettings):
    """Configuration thresholds and toggles for article cleaning."""

    min_cleaned_content_length: int = 25
    min_cleaned_words_count: int = 5
    max_consecutive_blank_lines: int = 2
    enable_html_cleaning: bool = True
    enable_boilerplate_cleaning: bool = True
    enable_unicode_normalization: bool = True
    enable_whitespace_normalization: bool = True
    enable_paragraph_cleanup: bool = True
    enable_repeated_paragraph_removal: bool = True

    model_config = {
        "env_prefix": "CLEANING_",
        "extra": "ignore",
    }


cleaning_config = CleaningConfig()
