"""Enums defining Step 3 content cleaning status."""
from enum import Enum


class CleaningStatus(str, Enum):
    """Status indicating the outcome of Step 3 content cleaning."""

    SUCCESS = "SUCCESS"
    CLEANING_FAILED = "CLEANING_FAILED"
