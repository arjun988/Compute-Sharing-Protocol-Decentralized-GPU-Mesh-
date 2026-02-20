"""
Layer 2: Job Scheduling
Handles job allocation, load balancing, and fault tolerance
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models import Job, Node, Task
from app.layers.node_registration import NodeRegistry
import uuid
import logging

logger = logging.getLogger(__name__)


class JobScheduler:
    """Job scheduling and allocation"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.node_registry = NodeRegistry(db)
    
    async def create_job(
        self,
        user_id: str,
        job_type: str,
        model: str,
        dataset: Optional[str] = None,
        budget: Optional[float] = None,
        speed: str = "balanced",
        metadata: Optional[Dict] = None
    ) -> Job:
        """Create a new job"""
        try:
            job = Job(
                job_id=f"job_{uuid.uuid4().hex[:12]}",
                user_id=user_id,
                job_type=job_type,
                model=model,
                dataset=dataset,
                budget=budget,
                speed=speed,
                status="pending",
                meta_data=metadata or {}
            )
            self.db.add(job)
            await self.db.commit()
            await self.db.refresh(job)
            logger.info(f"Job {job.job_id} created")
            return job
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating job: {e}")
            raise
    
    async def allocate_job(self, job_id: str) -> Optional[str]:
        """Allocate job to best available node"""
        try:
            # Get job
            result = await self.db.execute(
                select(Job).where(Job.job_id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job or job.status != "pending":
                logger.warning(f"Job {job_id} not found or not pending")
                return None
            
            # Get available nodes based on speed preference
            if job.speed == "fast":
                # Prioritize high compute score
                nodes = await self.node_registry.get_best_nodes(limit=5)
            elif job.speed == "cheap":
                # Prioritize low cost (high reputation, lower compute)
                nodes = await self.node_registry.get_active_nodes()
                nodes.sort(key=lambda n: (n.reputation, -n.compute_score))
                nodes = nodes[:5]
            else:  # balanced
                # Balance between compute and reputation
                nodes = await self.node_registry.get_best_nodes(limit=5)
            
            if not nodes:
                logger.warning(f"No available nodes for job {job_id}")
                return None
            
            # Select best node
            selected_node = nodes[0]
            
            # Update job
            await self.db.execute(
                update(Job)
                .where(Job.job_id == job_id)
                .values(
                    assigned_node=selected_node.node_id,
                    status="running",
                    started_at=datetime.utcnow()
                )
            )
            
            # Update node status
            await self.node_registry.update_node_status(selected_node.node_id, "busy")
            
            await self.db.commit()
            logger.info(f"Job {job_id} allocated to node {selected_node.node_id}")
            return selected_node.node_id
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error allocating job {job_id}: {e}")
            return None
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        try:
            result = await self.db.execute(
                select(Job).where(Job.job_id == job_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
            return None
    
    async def update_job_status(
        self,
        job_id: str,
        status: str,
        error_message: Optional[str] = None,
        cost: Optional[float] = None
    ) -> bool:
        """Update job status"""
        try:
            update_values = {"status": status}
            
            if status == "completed":
                update_values["completed_at"] = datetime.utcnow()
            elif status == "failed":
                update_values["error_message"] = error_message
            
            if cost is not None:
                update_values["cost"] = cost
            
            result = await self.db.execute(
                update(Job)
                .where(Job.job_id == job_id)
                .values(**update_values)
            )
            
            # Free up node if job is done
            if status in ["completed", "failed"]:
                job = await self.get_job(job_id)
                if job and job.assigned_node:
                    await self.node_registry.update_node_status(job.assigned_node, "active")
            
            await self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating job status {job_id}: {e}")
            return False
    
    async def retry_job(self, job_id: str) -> bool:
        """Retry a failed job"""
        try:
            job = await self.get_job(job_id)
            if not job or job.status != "failed":
                return False
            
            # Reset job
            await self.db.execute(
                update(Job)
                .where(Job.job_id == job_id)
                .values(
                    status="pending",
                    assigned_node=None,
                    started_at=None,
                    error_message=None
                )
            )
            await self.db.commit()
            
            # Re-allocate
            await self.allocate_job(job_id)
            logger.info(f"Job {job_id} retried")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error retrying job {job_id}: {e}")
            return False
    
    async def get_pending_jobs(self) -> List[Job]:
        """Get all pending jobs"""
        try:
            result = await self.db.execute(
                select(Job).where(Job.status == "pending")
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting pending jobs: {e}")
            return []
    
    async def check_timeout_jobs(self, timeout_seconds: int = 3600) -> List[str]:
        """Check for jobs that have timed out"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(seconds=timeout_seconds)
            result = await self.db.execute(
                select(Job).where(
                    Job.status == "running",
                    Job.started_at < cutoff_time
                )
            )
            timeout_jobs = list(result.scalars().all())
            
            job_ids = []
            for job in timeout_jobs:
                await self.update_job_status(
                    job.job_id,
                    "failed",
                    error_message="Job timeout"
                )
                job_ids.append(job.job_id)
            
            return job_ids
        except Exception as e:
            logger.error(f"Error checking timeout jobs: {e}")
            return []

