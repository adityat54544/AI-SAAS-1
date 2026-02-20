"""
Job service for background job queue management.
Interfaces with Redis queue for async job processing.
"""

import json
from datetime import datetime, timezone
from typing import Any, Optional

import redis

from app.config import settings
from app.supabase_client import supabase


class JobError(Exception):
    """Raised when job operations fail."""
    pass


class JobService:
    """
    Job queue management service.
    
    Handles job creation, status updates, and queue operations.
    Uses Redis for queue management and Supabase for persistence.
    """
    
    QUEUE_NAME = "autodevops:jobs"
    JOB_PREFIX = "autodevops:job:"
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize job service.
        
        Args:
            redis_url: Redis connection URL.
        """
        self.redis_url = redis_url or settings.redis_url
        self._redis: Optional[redis.Redis] = None
    
    @property
    def redis(self) -> redis.Redis:
        """Get Redis client (lazy initialization)."""
        if self._redis is None:
            self._redis = redis.from_url(
                self.redis_url,
                decode_responses=True,
            )
        return self._redis
    
    async def create_job(
        self,
        job_type: str,
        repository_id: str,
        payload: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Create a new job record and enqueue it.
        
        Args:
            job_type: Type of job (analysis, clone, sync, ci_generation).
            repository_id: UUID of the repository.
            payload: Optional job payload data.
        
        Returns:
            Created job record.
        
        Raises:
            JobError: If creation fails.
        """
        try:
            # Create job record in Supabase
            job_data = {
                "job_type": job_type,
                "repository_id": repository_id,
                "status": "queued",
                "progress": 0,
                "payload": payload,
            }
            
            response = supabase.table("jobs").insert(job_data).execute()
            
            if not response.data:
                raise JobError("Failed to create job record")
            
            job = response.data[0]
            
            # Enqueue job in Redis
            await self._enqueue_job(job["id"], job_type, repository_id, payload)
            
            return job
        
        except Exception as e:
            raise JobError(f"Failed to create job: {e}")
    
    async def _enqueue_job(
        self,
        job_id: str,
        job_type: str,
        repository_id: str,
        payload: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Add job to Redis queue.
        
        Args:
            job_id: UUID of the job.
            job_type: Type of job.
            repository_id: UUID of the repository.
            payload: Job payload data.
        """
        queue_item = {
            "id": job_id,
            "job_type": job_type,
            "repository_id": repository_id,
            "payload": payload,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        self.redis.lpush(self.QUEUE_NAME, json.dumps(queue_item))
    
    async def get_job(self, job_id: str) -> Optional[dict[str, Any]]:
        """
        Get a job record by ID.
        
        Args:
            job_id: UUID of the job.
        
        Returns:
            Job record or None if not found.
        """
        try:
            response = supabase.table("jobs").select("*").eq("id", job_id).execute()
            
            if response.data:
                return response.data[0]
            return None
        
        except Exception:
            return None
    
    async def get_jobs_by_repository(
        self,
        repository_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Get jobs for a repository.
        
        Args:
            repository_id: UUID of the repository.
            limit: Maximum number of records to return.
            offset: Number of records to skip.
        
        Returns:
            List of job records.
        """
        try:
            response = (
                supabase.table("jobs")
                .select("*")
                .eq("repository_id", repository_id)
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            
            return response.data or []
        
        except Exception:
            return []
    
    async def update_job_progress(
        self,
        job_id: str,
        progress: int,
        current_step: str,
    ) -> dict[str, Any]:
        """
        Update job progress.
        
        Args:
            job_id: UUID of the job.
            progress: Progress percentage (0-100).
            current_step: Description of current step.
        
        Returns:
            Updated job record.
        
        Raises:
            JobError: If update fails.
        """
        try:
            update_data = {
                "progress": min(100, max(0, progress)),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            response = (
                supabase.table("jobs")
                .update(update_data)
                .eq("id", job_id)
                .execute()
            )
            
            if not response.data:
                raise JobError(f"Job {job_id} not found")
            
            # Update Redis cache for progress
            self.redis.setex(
                f"{self.JOB_PREFIX}{job_id}:progress",
                3600,  # 1 hour TTL
                json.dumps({
                    "progress": progress,
                    "current_step": current_step,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }),
            )
            
            return response.data[0]
        
        except Exception as e:
            raise JobError(f"Failed to update job progress: {e}")
    
    async def start_job(self, job_id: str) -> dict[str, Any]:
        """
        Mark job as started (processing).
        
        Args:
            job_id: UUID of the job.
        
        Returns:
            Updated job record.
        """
        try:
            update_data = {
                "status": "processing",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            response = (
                supabase.table("jobs")
                .update(update_data)
                .eq("id", job_id)
                .execute()
            )
            
            if not response.data:
                raise JobError(f"Job {job_id} not found")
            
            return response.data[0]
        
        except Exception as e:
            raise JobError(f"Failed to start job: {e}")
    
    async def complete_job(
        self,
        job_id: str,
        result_data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Mark job as completed.
        
        Args:
            job_id: UUID of the job.
            result_data: Optional result data from job execution.
        
        Returns:
            Updated job record.
        """
        try:
            update_data = {
                "status": "completed",
                "progress": 100,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            if result_data:
                update_data["result_data"] = result_data
            
            response = (
                supabase.table("jobs")
                .update(update_data)
                .eq("id", job_id)
                .execute()
            )
            
            if not response.data:
                raise JobError(f"Job {job_id} not found")
            
            return response.data[0]
        
        except Exception as e:
            raise JobError(f"Failed to complete job: {e}")
    
    async def fail_job(
        self,
        job_id: str,
        error_message: str,
    ) -> dict[str, Any]:
        """
        Mark job as failed.
        
        Args:
            job_id: UUID of the job.
            error_message: Error message describing the failure.
        
        Returns:
            Updated job record.
        """
        try:
            update_data = {
                "status": "failed",
                "error_message": error_message,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            response = (
                supabase.table("jobs")
                .update(update_data)
                .eq("id", job_id)
                .execute()
            )
            
            if not response.data:
                raise JobError(f"Job {job_id} not found")
            
            return response.data[0]
        
        except Exception as e:
            raise JobError(f"Failed to fail job: {e}")
    
    async def cancel_job(self, job_id: str) -> dict[str, Any]:
        """
        Cancel a queued job.
        
        Args:
            job_id: UUID of the job.
        
        Returns:
            Updated job record.
        
        Raises:
            JobError: If job cannot be cancelled.
        """
        try:
            # Check if job can be cancelled
            job = await self.get_job(job_id)
            if not job:
                raise JobError(f"Job {job_id} not found")
            
            if job["status"] != "queued":
                raise JobError(f"Cannot cancel job with status: {job['status']}")
            
            update_data = {
                "status": "failed",
                "error_message": "Job cancelled by user",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            response = (
                supabase.table("jobs")
                .update(update_data)
                .eq("id", job_id)
                .execute()
            )
            
            if not response.data:
                raise JobError(f"Job {job_id} not found")
            
            return response.data[0]
        
        except Exception as e:
            raise JobError(f"Failed to cancel job: {e}")
    
    async def add_job_log(
        self,
        job_id: str,
        message: str,
        level: str = "info",
    ) -> None:
        """
        Add a log entry for a job.
        
        Args:
            job_id: UUID of the job.
            message: Log message.
            level: Log level (debug, info, warning, error).
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
        }
        
        self.redis.rpush(
            f"{self.JOB_PREFIX}{job_id}:logs",
            json.dumps(log_entry),
        )
    
    async def get_job_logs(
        self,
        job_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get logs for a job.
        
        Args:
            job_id: UUID of the job.
            limit: Maximum number of logs to return.
        
        Returns:
            List of log entries.
        """
        logs = self.redis.lrange(
            f"{self.JOB_PREFIX}{job_id}:logs",
            -limit,
            -1,
        )
        
        return [json.loads(log) for log in logs]
    
    def get_queue_length(self) -> int:
        """
        Get the number of jobs in the queue.
        
        Returns:
            Number of queued jobs.
        """
        return self.redis.llen(self.QUEUE_NAME)


# Singleton instance
_job_service: Optional[JobService] = None


def get_job_service() -> JobService:
    """Get the singleton job service instance."""
    global _job_service
    if _job_service is None:
        _job_service = JobService()
    return _job_service