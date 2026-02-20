"""
Tasks for distributed job execution (works with or without Celery/Redis)
"""
try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    Celery = None

from app.config import settings
from app.database import AsyncSessionLocal
from app.layers import JobScheduler, ContainerManager, PaymentManager, ReputationManager
from app.models import Task, Job, Payment
from sqlalchemy import select
from datetime import datetime
from typing import Optional
import uuid
import logging
import time
import numpy as np
import sys

logger = logging.getLogger(__name__)

# Initialize Celery (optional - will work without it)
celery_app = None
if CELERY_AVAILABLE:
    try:
        celery_app = Celery(
            "openmesh",
            broker=settings.celery_broker_url,
            backend=settings.celery_result_backend
        )
        
        # Windows compatibility: use 'solo' pool instead of 'prefork'
        pool_type = "solo" if sys.platform == "win32" else "prefork"
        
        celery_app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone="UTC",
            enable_utc=True,
            worker_pool=pool_type,
        )
        logger.info("Celery initialized successfully")
    except Exception as e:
        logger.warning(f"Celery not available (Redis may not be running), tasks will run synchronously: {e}")
        celery_app = None
else:
    logger.info("Celery not installed, tasks will run synchronously")


def simulate_training(duration: float, complexity: int = 1):
    """Simulate training workload"""
    start_time = time.time()
    
    # Simulate CPU-intensive work
    iterations = int(duration * complexity * 1000)
    for _ in range(iterations):
        # Matrix multiplication simulation
        a = np.random.rand(100, 100)
        b = np.random.rand(100, 100)
        _ = np.dot(a, b)
    
    elapsed = time.time() - start_time
    return {
        "status": "completed",
        "duration": elapsed,
        "iterations": iterations
    }


def execute_finetune_task(
    task_id: str,
    job_id: str,
    node_id: str,
    model: str,
    dataset: Optional[str] = None,
    duration: float = 10.0
):
    """Execute a finetuning task (can be called directly or via Celery)"""
    logger.info(f"Starting finetune task {task_id} for job {job_id}")
    
    try:
        # Simulate training
        result = simulate_training(duration, complexity=2)
        
        # Update task status in database
        async def update_task():
            async with AsyncSessionLocal() as session:
                from sqlalchemy import update
                await session.execute(
                    update(Task)
                    .where(Task.task_id == task_id)
                    .values(
                        status="completed",
                        completed_at=datetime.utcnow(),
                        duration=result["duration"]
                    )
                )
                await session.commit()
        
        import asyncio
        asyncio.run(update_task())
        
        logger.info(f"Task {task_id} completed successfully")
        return {
            "task_id": task_id,
            "status": "completed",
            "result": result
        }
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        
        # Update task status
        async def update_task():
            async with AsyncSessionLocal() as session:
                from sqlalchemy import update
                await session.execute(
                    update(Task)
                    .where(Task.task_id == task_id)
                    .values(
                        status="failed",
                        completed_at=datetime.utcnow()
                    )
                )
                await session.commit()
        
        import asyncio
        asyncio.run(update_task())
        
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(e)
        }


def process_job(job_id: str):
    """Process a job by creating and executing tasks (can be called directly or via Celery)"""
    logger.info(f"Processing job {job_id}")
    
    async def process():
        async with AsyncSessionLocal() as session:
            # Get job
            result = await session.execute(
                select(Job).where(Job.job_id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            scheduler = JobScheduler(session)
            container_manager = ContainerManager()
            
            # Allocate job to node
            node_id = await scheduler.allocate_job(job_id)
            if not node_id:
                logger.error(f"Failed to allocate job {job_id}")
                await scheduler.update_job_status(job_id, "failed", "No available nodes")
                return
            
            # Create task
            task = Task(
                task_id=f"task_{uuid.uuid4().hex[:12]}",
                job_id=job_id,
                node_id=node_id,
                status="pending"
            )
            session.add(task)
            await session.commit()
            await session.refresh(task)
            
            # Create container (optional, can be skipped for simulation)
            container_id = None
            try:
                container_id = container_manager.create_container(
                    task_id=task.task_id,
                    job_type=job.job_type,
                    model=job.model,
                    dataset=job.dataset
                )
                if container_id:
                    task.container_id = container_id
                    task.status = "running"
                    task.started_at = datetime.utcnow()
                    await session.commit()
            except Exception as e:
                logger.warning(f"Container creation failed, continuing without: {e}")
            
            # Execute task
            duration = 30.0  # Default duration
            if job.speed == "fast":
                duration = 10.0
            elif job.speed == "cheap":
                duration = 60.0
            
            # Execute task (with or without Celery)
            if celery_app:
                # Register as Celery task if not already
                if not hasattr(execute_finetune_task, 'delay'):
                    execute_finetune_task_celery = celery_app.task(name="execute_finetune_task")(execute_finetune_task)
                    execute_finetune_task_celery.delay(
                        task_id=task.task_id,
                        job_id=job_id,
                        node_id=node_id,
                        model=job.model,
                        dataset=job.dataset,
                        duration=duration
                    )
                else:
                    execute_finetune_task.delay(
                        task_id=task.task_id,
                        job_id=job_id,
                        node_id=node_id,
                        model=job.model,
                        dataset=job.dataset,
                        duration=duration
                    )
                logger.info(f"Job {job_id} task {task.task_id} queued to Celery")
            else:
                # Run synchronously
                execute_finetune_task(
                    task_id=task.task_id,
                    job_id=job_id,
                    node_id=node_id,
                    model=job.model,
                    dataset=job.dataset,
                    duration=duration
                )
                logger.info(f"Job {job_id} task {task.task_id} executed synchronously")
    
    import asyncio
    asyncio.run(process())


def monitor_jobs():
    """Monitor running jobs and check for completion/timeout (can be called directly or via Celery)"""
    async def monitor():
        async with AsyncSessionLocal() as session:
            scheduler = JobScheduler(session)
            payment_manager = PaymentManager(session)
            reputation_manager = ReputationManager(session)
            
            # Check timeout jobs
            timeout_jobs = await scheduler.check_timeout_jobs(timeout_seconds=3600)
            
            # Check completed tasks
            result = await session.execute(
                select(Task).where(Task.status == "completed")
            )
            completed_tasks = result.scalars().all()
            
            for task in completed_tasks:
                # Check if job is complete
                job_result = await session.execute(
                    select(Job).where(Job.job_id == task.job_id)
                )
                job = job_result.scalar_one_or_none()
                
                if job and job.status == "running":
                    # Calculate cost
                    cost = 0.1 * (task.duration or 0) / 60  # $0.1 per minute
                    
                    # Check budget
                    if job.budget and cost > job.budget:
                        await scheduler.update_job_status(
                            job.job_id,
                            "failed",
                            "Budget exceeded"
                        )
                        continue
                    
                    # Update job
                    await scheduler.update_job_status(
                        job.job_id,
                        "completed",
                        cost=cost
                    )
                    
                    # Create and complete payment
                    if job.assigned_node:
                        payment = await payment_manager.create_payment(
                            job_id=job.job_id,
                            node_id=job.assigned_node,
                            user_id=job.user_id,
                            amount=cost
                        )
                        await payment_manager.complete_payment(payment.transaction_id)
                        
                        # Update reputation
                        await reputation_manager.reward_node(
                            job.assigned_node,
                            job.job_id,
                            success=True
                        )
            
            # Check failed tasks
            result = await session.execute(
                select(Task).where(Task.status == "failed")
            )
            failed_tasks = result.scalars().all()
            
            for task in failed_tasks:
                job_result = await session.execute(
                    select(Job).where(Job.job_id == task.job_id)
                )
                job = job_result.scalar_one_or_none()
                
                if job and job.status == "running":
                    await scheduler.update_job_status(
                        job.job_id,
                        "failed",
                        "Task execution failed"
                    )
                    
                    if job.assigned_node:
                        await reputation_manager.reward_node(
                            job.assigned_node,
                            job.job_id,
                            success=False
                        )
    
    import asyncio
    asyncio.run(monitor())


# Register as Celery tasks if Celery is available
if celery_app:
    execute_finetune_task = celery_app.task(name="execute_finetune_task")(execute_finetune_task)
    process_job = celery_app.task(name="process_job")(process_job)
    monitor_jobs = celery_app.task(name="monitor_jobs")(monitor_jobs)
