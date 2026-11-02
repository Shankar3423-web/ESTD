"""Database engine, session management, and Base definition for ESTD."""
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from backend.common.config.settings import get_settings
from backend.common.logging.logger import logger

Base = declarative_base()

_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


def get_engine() -> Engine:
    """Return singleton SQLAlchemy engine configured from settings."""
    global _engine
    if _engine is None:
        settings = get_settings()
        if hasattr(settings, "get_database_url"):
            db_url = settings.get_database_url()
        else:
            db_url = getattr(settings, "database_url", None) or "postgresql://postgres:root@localhost:5433/estd_knowledge"

        safe_url = settings.get_safe_database_url() if hasattr(settings, "get_safe_database_url") else (db_url.split('@')[-1] if '@' in db_url else 'configured DB')
        logger.info(f"Initializing database engine for: {safe_url}")
        
        # Determine pool parameters based on dialect
        connect_args = {}
        if db_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
            _engine = create_engine(
                db_url,
                connect_args=connect_args,
                echo=False,
            )
        else:
            _engine = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                echo=False,
            )
    return _engine



def get_session_factory() -> sessionmaker:
    """Return singleton sessionmaker bound to current engine."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            bind=engine,
        )
    return _session_factory



@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error(f"Database session rolled back due to error: {exc}")
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a database session."""
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error(f"Database session rolled back: {exc}")
        raise
    finally:
        session.close()


def init_db(engine: Optional[Engine] = None) -> None:
    """Create all database tables defined in metadata and run schema checks."""
    target_engine = engine or get_engine()
    logger.info("Ensuring all database tables exist in metadata...")
    Base.metadata.create_all(bind=target_engine)

    # Ensure likes_count column and article_likes table exist
    try:
        from sqlalchemy import text
        with target_engine.begin() as conn:
            conn.execute(text("""
                ALTER TABLE news_articles 
                ADD COLUMN IF NOT EXISTS likes_count INTEGER DEFAULT 0 NOT NULL;
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS article_likes (
                    id SERIAL PRIMARY KEY,
                    article_id BIGINT NOT NULL REFERENCES news_articles(id) ON DELETE CASCADE,
                    client_id VARCHAR(128) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    CONSTRAINT uq_article_client_like UNIQUE (article_id, client_id)
                );
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_article_likes_article_id ON article_likes(article_id);
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_article_likes_client_id ON article_likes(client_id);
            """))
    except Exception as exc:
        logger.warning(f"Notice on ensuring likes schema: {exc}")

    logger.info("Database tables initialized successfully.")


def close_engine() -> None:
    """Dispose the current engine and clear session factory."""
    global _engine, _session_factory
    if _engine is not None:
        logger.info("Disposing database engine pool.")
        _engine.dispose()
        _engine = None
    _session_factory = None


def check_db_health(engine: Optional[Engine] = None) -> dict:
    """Execute 'SELECT 1' to verify active database connectivity and return status details."""
    from sqlalchemy import text
    target_engine = engine or get_engine()
    with target_engine.connect() as conn:
        result = conn.execute(text("SELECT 1;")).scalar()
        if result != 1:
            raise RuntimeError("Database health check query returned unexpected result.")
        
        # Query current database and server version if postgresql
        db_name = None
        server_version = None
        try:
            info_row = conn.execute(text("SELECT current_database(), version();")).fetchone()
            if info_row:
                db_name = info_row[0]
                server_version = info_row[1].split()[0] + " " + info_row[1].split()[1] if info_row[1] else None
        except Exception:
            pass

    return {
        "status": "healthy",
        "database": "connected",
        "database_name": db_name or "estd_knowledge",
        "server_version": server_version,
    }

