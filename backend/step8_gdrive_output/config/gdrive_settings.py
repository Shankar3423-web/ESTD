"""Configuration settings for Step 8 Google Drive and Google Docs output pipeline."""
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.common.config.settings import ENV_FILE_PATH
from backend.common.constants.categories import ESTDCategory

FINAL_CATEGORIES: Tuple[str, ...] = tuple(category.value for category in ESTDCategory)

ROOT_FOLDER_NAME = "ESTD CONTENT"


class Step8Settings(BaseSettings):
    """Configuration settings for Step 8 Drive folder hierarchy and document creation."""

    root_folder_name: str = Field(default=ROOT_FOLDER_NAME, alias="GDRIVE_ROOT_FOLDER_NAME")
    root_folder_id: Optional[str] = Field(default=None, alias="ESTD_CONTENT_ROOT_FOLDER_ID")
    entertainment_folder_id: Optional[str] = Field(default=None, alias="ENTERTAINMENT_FOLDER_ID")
    sports_folder_id: Optional[str] = Field(default=None, alias="SPORTS_FOLDER_ID")
    tech_folder_id: Optional[str] = Field(default=None, alias="TECH_FOLDER_ID")
    developments_folder_id: Optional[str] = Field(default=None, alias="DEVELOPMENTS_FOLDER_ID")
    business_finance_folder_id: Optional[str] = Field(default=None, alias="BUSINESS_FINANCE_FOLDER_ID")

    # Legacy category folder IDs preserved for backward compatibility
    ai_folder_id: Optional[str] = Field(default=None, alias="ARTIFICIAL_INTELLIGENCE_FOLDER_ID")
    technology_folder_id: Optional[str] = Field(default=None, alias="TECHNOLOGY_FOLDER_ID")
    business_folder_id: Optional[str] = Field(default=None, alias="BUSINESS_FOLDER_ID")
    education_folder_id: Optional[str] = Field(default=None, alias="EDUCATION_FOLDER_ID")
    science_folder_id: Optional[str] = Field(default=None, alias="SCIENCE_FOLDER_ID")

    timeout_seconds: float = Field(default=25.0, alias="GDRIVE_TIMEOUT_SECONDS")
    max_retries: int = Field(default=3, alias="GDRIVE_MAX_RETRIES")
    retry_backoff_factor: float = Field(default=1.5, alias="GDRIVE_RETRY_BACKOFF")

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def finalized_categories(self) -> Tuple[str, ...]:
        """The 5 finalized ESTD categories."""
        return FINAL_CATEGORIES


@lru_cache()
def get_step8_settings() -> Step8Settings:
    """Return cached singleton instance of Step8Settings."""
    return Step8Settings()
