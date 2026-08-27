"""
Lightweight In-Memory Background Job Execution & Status Management Abstraction.
Allows async execution of long-running operations (ingestion, bulk prediction, report generation)
with thread-safe status tracking and worker boundary easily replaceable by Celery / Redis.
"""

import uuid
import time
import threading
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timezone
from backend.core.logging import logger


class JobStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class BackgroundJobManager:
    """Thread-safe background job registry and task status tracker."""
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create_job(self, job_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Creates and registers a new job entry in PENDING state."""
        job_id = f"JOB_{job_type[:4].upper()}_{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "job_type": job_type,
                "status": JobStatus.PENDING,
                "progress": 0.0,
                "metadata": metadata or {},
                "result": None,
                "error": None,
                "created_at": now_iso,
                "updated_at": now_iso
            }
        logger.info(f"Background job '{job_id}' ({job_type}) registered.")
        return job_id

    def update_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        result: Optional[Any] = None,
        error: Optional[str] = None
    ) -> None:
        """Updates job status, progress percentage, or execution results."""
        with self._lock:
            if job_id not in self._jobs:
                return
            job = self._jobs[job_id]
            if status:
                job["status"] = status
            if progress is not None:
                job["progress"] = min(100.0, max(0.0, float(progress)))
            if result is not None:
                job["result"] = result
            if error is not None:
                job["error"] = error
            job["updated_at"] = datetime.now(timezone.utc).isoformat()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves background job status record."""
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    def execute_async(self, job_id: str, func: Callable, *args, **kwargs) -> None:
        """Runs the given target function in a background worker thread."""
        def worker():
            try:
                self.update_job(job_id, status=JobStatus.PROCESSING, progress=10.0)
                res = func(*args, **kwargs)
                self.update_job(job_id, status=JobStatus.COMPLETED, progress=100.0, result=res)
            except Exception as e:
                logger.error(f"Background job '{job_id}' failed: {str(e)}", exc_info=True)
                self.update_job(job_id, status=JobStatus.FAILED, progress=100.0, error=str(e))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()


# Global Background Job Manager Instance
job_manager = BackgroundJobManager()
