"""
FastAPI routes
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.layers import (
    NodeRegistry,
    JobScheduler,
    MonitoringService,
    PaymentManager,
    ReputationManager
)
from app.api.schemas import (
    NodeRegisterRequest,
    NodeResponse,
    FinetuneRequest,
    JobResponse,
    SystemStatsResponse,
    HealthResponse
)
from app.tasks import process_job
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/nodes/register", response_model=NodeResponse)
async def register_node(
    request: NodeRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new node"""
    registry = NodeRegistry(db)
    node = await registry.register_node(
        node_id=request.node_id,
        host=request.host,
        port=request.port,
        gpu_memory=request.gpu_memory,
        compute_score=request.compute_score,
        metadata=request.metadata
    )
    return node


@router.get("/nodes", response_model=List[NodeResponse])
async def list_nodes(db: AsyncSession = Depends(get_db)):
    """List all active nodes"""
    registry = NodeRegistry(db)
    nodes = await registry.get_active_nodes()
    return nodes


@router.get("/nodes/{node_id}", response_model=NodeResponse)
async def get_node(node_id: str, db: AsyncSession = Depends(get_db)):
    """Get node details"""
    registry = NodeRegistry(db)
    node = await registry.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.post("/nodes/{node_id}/heartbeat")
async def heartbeat(node_id: str, db: AsyncSession = Depends(get_db)):
    """Update node heartbeat"""
    registry = NodeRegistry(db)
    success = await registry.update_heartbeat(node_id)
    if not success:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"status": "ok"}


@router.post("/finetune", response_model=JobResponse)
async def create_finetune_job(
    request: FinetuneRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Create a finetuning job"""
    scheduler = JobScheduler(db)
    
    job = await scheduler.create_job(
        user_id=request.user_id,
        job_type="finetune",
        model=request.model,
        dataset=request.dataset,
        budget=request.max_budget,
        speed=request.speed,
        metadata=request.metadata
    )
    
    # Process job in background (or synchronously if Celery not available)
    try:
        from app.tasks import process_job, celery_app
        if celery_app and hasattr(process_job, 'delay'):
            # Use Celery if available
            process_job.delay(job.job_id)
        else:
            # Fallback to synchronous execution via background task
            background_tasks.add_task(process_job, job.job_id)
    except Exception as e:
        logger.warning(f"Could not queue job, will process synchronously: {e}")
        from app.tasks import process_job
        background_tasks.add_task(process_job, job.job_id)
    
    return job


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get job details"""
    scheduler = JobScheduler(db)
    job = await scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/jobs/{job_id}/retry")
async def retry_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Retry a failed job"""
    scheduler = JobScheduler(db)
    success = await scheduler.retry_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Job cannot be retried")
    return {"status": "ok", "message": "Job queued for retry"}


@router.get("/stats", response_model=SystemStatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get system statistics"""
    monitoring = MonitoringService(db)
    stats = await monitoring.get_system_stats()
    return stats


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """System health check"""
    monitoring = MonitoringService(db)
    health = await monitoring.health_check()
    return health


@router.get("/nodes/{node_id}/metrics")
async def get_node_metrics(node_id: str, db: AsyncSession = Depends(get_db)):
    """Get node metrics"""
    monitoring = MonitoringService(db)
    metrics = await monitoring.get_node_metrics(node_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Node not found")
    return metrics


@router.get("/jobs/{job_id}/metrics")
async def get_job_metrics(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get job metrics"""
    monitoring = MonitoringService(db)
    metrics = await monitoring.get_job_metrics(job_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Job not found")
    return metrics

