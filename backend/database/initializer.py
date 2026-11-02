"""Database creation, initialization, and verification utilities for ESTD."""
import logging
from typing import Optional

import psycopg
from psycopg import sql

from backend.common.config.settings import get_settings
from backend.common.logging.logger import logger
from backend.database.connection.session import Base, get_engine, init_db


def ensure_database_exists(
    host: Optional[str] = None,
    port: Optional[int] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    target_db: Optional[str] = None,
    maintenance_db: str = "postgres",
) -> bool:
    """Check if the target database exists on the PostgreSQL server, creating it if absent.
    
    Returns:
        True if the database existed or was successfully created.
    Raises:
        psycopg.Error: If the server cannot be contacted or lacks permissions.
    """
    settings = get_settings()
    effective_host = host or settings.postgres_host
    effective_port = port or settings.postgres_port
    effective_user = user or settings.postgres_user
    effective_password = (
        password
        or (settings.postgres_password.get_secret_value() if settings.postgres_password else "root")
    )
    effective_target_db = target_db or settings.postgres_db

    logger.info(
        f"Verifying PostgreSQL target database '{effective_target_db}' on {effective_host}:{effective_port}..."
    )

    try:
        # Connect to maintenance database with autocommit enabled (required for CREATE DATABASE)
        conn_str = f"host={effective_host} port={effective_port} user={effective_user} password={effective_password} dbname={maintenance_db}"
        with psycopg.connect(conn_str, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s;",
                    (effective_target_db,),
                )
                exists = cur.fetchone() is not None
                if not exists:
                    logger.info(f"Database '{effective_target_db}' does not exist. Creating database...")
                    # Use sql.Identifier to safely quote database name and avoid SQL injection
                    cur.execute(sql.SQL("CREATE DATABASE {};").format(sql.Identifier(effective_target_db)))
                    logger.info(f"Database '{effective_target_db}' created successfully.")
                else:
                    logger.info(f"Database '{effective_target_db}' already exists.")
        return True
    except psycopg.errors.InsufficientPrivilege as priv_err:
        logger.error(
            f"Insufficient privileges for user '{effective_user}' to create database '{effective_target_db}': {priv_err}"
        )
        raise
    except psycopg.Error as db_err:
        logger.error(
            f"Failed to connect to PostgreSQL server {effective_host}:{effective_port} to verify database: {db_err}"
        )
        raise


def setup_knowledge_database() -> None:
    """Full database setup routine: verify database existence, create tables, and seed categories."""
    ensure_database_exists()
    init_db()
    from backend.database.repositories.category_repository import CategoryRepository
    from backend.database.connection.session import get_db_session
    with get_db_session() as session:
        CategoryRepository.seed_categories(session)
        logger.info("Category seeding completed during database setup.")
