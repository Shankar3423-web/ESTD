"""Pydantic models for ESTD Pipeline Orchestration and Verification Dashboard."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StepStatus(str, Enum):
    """Lifecycle status of an individual pipeline step."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class PipelineJobStatus(str, Enum):
    """Lifecycle status of a pipeline execution job."""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class StepDetail(BaseModel):
    """Execution status and audit message for a pipeline step."""
    step_number: int
    name: str
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    details: Optional[str] = None


class SourceProviderStatus(BaseModel):
    """Health and article yield from a specific news source provider."""
    provider: str
    name: str
    status: str = "PENDING"  # PENDING, CONNECTED, WARNING, FAILED
    count: int = 0
    error: Optional[str] = None


class PipelineMetrics(BaseModel):
    """Accurate step-by-step metrics reflecting backend execution."""
    fetched: int = 0
    scraped: int = 0
    cleaned: int = 0
    duplicates_removed: int = 0
    stored_in_postgres: int = 0
    ai_generated: int = 0
    docs_created: int = 0
    failed: int = 0


class PipelineRunRequest(BaseModel):
    """Parameters for initiating a pipeline execution run."""
    categories: Optional[List[str]] = Field(
        default=None,
        description="Optional list of categories to process. Defaults to all 5 valid categories.",
    )
    target_per_category: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Number of articles to target per category (default 1 for responsive verification).",
    )


class PipelineJobResponse(BaseModel):
    """Real-time execution status of a pipeline run job."""
    job_id: str
    status: PipelineJobStatus
    current_step: str
    progress: int = Field(default=0, ge=0, le=100)
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    steps: Dict[str, StepDetail]
    sources: Dict[str, SourceProviderStatus]
    metrics: PipelineMetrics
    last_error: Optional[str] = None


class ArticleGoogleDocInfo(BaseModel):
    """Google Document reference and status for an article."""
    status: str
    document_id: Optional[str] = None
    document_url: Optional[str] = None
    category: str
    completed_at: Optional[datetime] = None


class ArticleCardItem(BaseModel):
    """Unified article representation for dashboard presentation."""
    id: int
    title: str
    category: str
    source_name: Optional[str] = None
    source_type: str
    url: str
    published_at: Optional[datetime] = None
    created_at: datetime
    content_snippet: str
    content: Optional[str] = None
    executive_summary: Optional[str] = None
    image_url: Optional[str] = None
    subcategory: Optional[str] = None
    ai_status: str
    pipeline_status: str
    likes_count: int = 0
    google_doc: Optional[ArticleGoogleDocInfo] = None
    video_rail: Optional[List[Dict[str, Any]]] = None


class ArticleListDashboardResponse(BaseModel):
    """Response containing list of processed articles for dashboard."""
    total: int
    items: List[ArticleCardItem]


class SystemOverviewResponse(BaseModel):
    """Health and summary counts for all subsystems in the dashboard."""
    postgres: Dict[str, Any]
    mcp: Dict[str, Any]
    gemini: Dict[str, Any]
    google_drive: Dict[str, Any]
    last_run: Optional[Dict[str, Any]] = None
    is_pipeline_running: bool = False
    active_job_id: Optional[str] = None


class AskIntelligenceResponse(BaseModel):
    """Response model for Ask ESTD AI search and intelligence synthesis."""
    query: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    headline: str
    answer: str
    key_takeaways: List[str] = []
    suggested_topics: List[str] = []
    has_estd_articles: bool = False
    articles_count: int = 0
    articles: List[ArticleCardItem] = []
    confidence_score: float = 0.95
    source_model: str = "gemini-2.5-flash"
    cached: bool = False

