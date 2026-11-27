"""Automated background scheduler for the ESTD Content Engine.

Executes periodic news collection, extraction, deduplication, and
Gemini AI content synthesis at configured intervals.
"""
import asyncio
from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, Optional

from backend.common.config.settings import get_settings
from backend.pipeline.orchestrator import pipeline_orchestrator

logger = logging.getLogger("estd.pipeline.scheduler")


class ContentEngineScheduler:
    """Manages the background scheduled execution of the ESTD content pipeline."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        self._task: Optional[asyncio.Task] = None
        self._running: bool = False
        self.last_run_at: Optional[datetime] = None
        self.next_run_at: Optional[datetime] = None
        self.last_run_status: str = "IDLE"
        self.total_runs: int = 0
        self.last_digest_run_at: Optional[datetime] = None
        self.last_digest_status: str = "IDLE"

    async def trigger_daily_digest(self, dry_run: bool = False, force: bool = False) -> Dict[str, Any]:
        """Trigger an immediate Daily Category Digest compilation in a non-blocking thread."""
        from backend.step8_gdrive_output.services.daily_digest_service import DailyDigestService

        logger.info(f"[Scheduler] Triggering Daily Digest compilation (dry_run={dry_run}, force={force})...")
        self.last_digest_status = "RUNNING"
        self.last_digest_run_at = datetime.now(timezone.utc)

        def _run():
            service = DailyDigestService()
            return service.generate_all_digests_for_date(dry_run=dry_run, force=force)

        try:
            res = await asyncio.to_thread(_run)
            self.last_digest_status = "COMPLETED" if res.get("failed_categories", 0) == 0 else "PARTIAL_ERROR"
            return res
        except Exception as exc:
            logger.error(f"[Scheduler] Error running Daily Digest: {exc}", exc_info=True)
            self.last_digest_status = f"ERROR:{str(exc)[:50]}"
            raise

    def is_running(self) -> bool:
        """Check if scheduler loop is active."""
        return self._running and self._task is not None and not self._task.done()

    def get_status(self) -> Dict[str, Any]:
        """Return real-time scheduler state and metrics."""
        settings = get_settings()
        return {
            "enabled": settings.enable_scheduler,
            "status": "RUNNING" if self.is_running() else ("OFF" if not settings.enable_scheduler else "IDLE"),
            "is_running": self.is_running(),
            "interval_hours": settings.scheduler_interval_hours,
            "last_run_at": self.last_run_at,
            "next_run_at": self.next_run_at if settings.enable_scheduler else None,
            "last_run_status": self.last_run_status,
            "total_runs": self.total_runs,
            "daily_digest_enabled": settings.enable_daily_digest,
            "last_digest_run_at": self.last_digest_run_at,
            "last_digest_status": self.last_digest_status,
        }

    async def start(self):
        """Start the automated scheduler loop."""
        settings = get_settings()
        if not settings.enable_scheduler:
            self.last_run_status = "OFF"
            logger.info("[Scheduler] Automated background news ingestion is OFF (ENABLE_SCHEDULER=off in .env).")
            return

        if self.is_running():
            logger.warning("[Scheduler] Scheduler is already active.")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            f"[Scheduler] Background news ingestion started. Interval: every {settings.scheduler_interval_hours} hour(s)."
        )

    async def stop(self):
        """Gracefully stop the background scheduler."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[Scheduler] Background news ingestion stopped.")

    async def _run_loop(self):
        """Main periodic scheduling loop."""
        settings = get_settings()
        interval_seconds = max(300, settings.scheduler_interval_hours * 3600)  # Min 5 min

        # Initial warm-up delay of 5 minutes so cold starts prioritize live user requests
        self.next_run_at = datetime.now(timezone.utc) + timedelta(seconds=300)
        await asyncio.sleep(300)

        while self._running:
            try:
                if not pipeline_orchestrator.is_running():
                    logger.info("[Scheduler] Triggering automated news pipeline run...")
                    self.last_run_at = datetime.now(timezone.utc)
                    self.last_run_status = "RUNNING"
                    
                    job = pipeline_orchestrator.create_job(
                        target_per_category=settings.scheduler_articles_per_category,
                    )
                    self.total_runs += 1
                    self.last_run_status = f"JOB_QUEUED:{job.job_id}"
                    logger.info(f"[Scheduler] Automated pipeline job {job.job_id} dispatched.")
                else:
                    logger.warning("[Scheduler] Previous pipeline run still active. Skipping interval.")
                    self.last_run_status = "SKIPPED_PREVIOUS_ACTIVE"

                # Synchronize ESTDPOD YouTube Channel uploads in background
                try:
                    from backend.step9_video_rail.services.estdpod_sync_service import EstdpodSyncService
                    logger.info("[Scheduler] Checking @ESTDPOD YouTube channel for new episodes...")
                    sync_svc = EstdpodSyncService()
                    await asyncio.to_thread(sync_svc.sync_channel, force_refresh=False)
                except Exception as estdpod_exc:
                    logger.warning(f"[Scheduler] ESTDPOD sync notice: {estdpod_exc}")

            except Exception as exc:
                logger.error(f"[Scheduler] Error during scheduled pipeline execution: {exc}")
                self.last_run_status = f"ERROR:{str(exc)[:60]}"

            # Evaluate end-of-day category digest compilation if enabled
            if settings.enable_daily_digest:
                try:
                    now_utc = datetime.now(timezone.utc)
                    today_date = now_utc.date()
                    if self.last_digest_run_at is None or self.last_digest_run_at.date() < today_date:
                        target_parts = settings.daily_digest_time.split(":")
                        target_hour = int(target_parts[0]) if len(target_parts) > 0 else 23
                        target_min = int(target_parts[1]) if len(target_parts) > 1 else 59
                        if (now_utc.hour > target_hour) or (now_utc.hour == target_hour and now_utc.minute >= target_min):
                            asyncio.create_task(self.trigger_daily_digest(dry_run=False, force=False))
                except Exception as digest_exc:
                    logger.warning(f"[Scheduler] Daily Digest evaluation notice: {digest_exc}")

            # Calculate next run time and await next interval
            self.next_run_at = datetime.now(timezone.utc) + timedelta(seconds=interval_seconds)
            logger.info(
                f"[Scheduler] Pipeline cycle complete. Next scheduled execution at: "
                f"{self.next_run_at.isoformat()} (in {settings.scheduler_interval_hours} hour(s))."
            )
            try:
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break


# Singleton instance
content_scheduler = ContentEngineScheduler()

