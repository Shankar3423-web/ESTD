"""SQLAlchemy model for tracking story likes per article and client."""
from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from backend.database.connection.session import Base


class ArticleLike(Base):
    """Stores individual like interactions per article and client identifier."""
    __tablename__ = "article_likes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(
        BigInteger,
        ForeignKey("news_articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_id = Column(String(128), nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("article_id", "client_id", name="uq_article_client_like"),
        Index("ix_article_likes_article_id", "article_id"),
        Index("ix_article_likes_client_id", "client_id"),
    )

    def __repr__(self) -> str:
        return f"<ArticleLike(article_id={self.article_id}, client_id='{self.client_id}')>"
