"""Programmatic runner for Alembic database migrations."""
from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config

from backend.common.config.settings import get_settings
from backend.common.logging.logger import logger


def get_alembic_config(db_url: Optional[str] = None) -> Config:
    """Build and return an Alembic Config object."""
    backend_dir = Path(__file__).resolve().parent.parent.parent
    ini_path = backend_dir / "alembic.ini"
    alembic_cfg = Config(str(ini_path))
    
    settings = get_settings()
    effective_url = db_url or (
        settings.get_database_url() if hasattr(settings, "get_database_url")
        else getattr(settings, "database_url", None)
    )
    if effective_url:
        alembic_cfg.set_main_option("sqlalchemy.url", effective_url)
    return alembic_cfg


def run_migrations(target_revision: str = "head", db_url: Optional[str] = None) -> None:
    """Apply Alembic migrations up to target revision (default 'head')."""
    logger.info(f"Running database migrations to '{target_revision}'...")
    cfg = get_alembic_config(db_url=db_url)
    command.upgrade(cfg, target_revision)
    logger.info(f"Database migrations applied successfully to '{target_revision}'.")


def rollback_migrations(target_revision: str = "base", db_url: Optional[str] = None) -> None:
    """Downgrade Alembic migrations down to target revision."""
    logger.info(f"Rolling back database migrations to '{target_revision}'...")
    cfg = get_alembic_config(db_url=db_url)
    command.downgrade(cfg, target_revision)
    logger.info(f"Database migrations rolled back to '{target_revision}'.")
