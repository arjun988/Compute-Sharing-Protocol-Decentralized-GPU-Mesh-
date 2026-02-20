"""
Layer 5: Monitoring
Handles system monitoring, metrics, and health checks
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import Node, Job, Task, Payment
from app.layers.node_registration import NodeRegistry
import logging

logger = logging.getLogger(__name__)


class MonitoringService:
    """System monitoring and metrics"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.node_registry = NodeRegistry(db)
    
    async def get_system_stats(self) -> Dict:
        """Get overall system statistics"""
        try:
            # Node statistics
            node_result = await self.db.execute(
                select(func.count(Node.id), func.avg(Node.reputation), func.avg(Node.compute_score))
            )
            node_stats = node_result.first()
            
            # Job statistics
            job_result = await self.db.execute(
                select(
                    func.count(Job.id),
                    func.sum(func.case((Job.status == "running", 1), else_=0)),
                    func.sum(func.case((Job.status == "completed", 1), else_=0)),
                    func.sum(func.case((Job.status == "failed", 1), else_=0))
                )
            )
            job_stats = job_result.first()
            
            # Payment statistics
            payment_result = await self.db.execute(
                select(func.sum(Payment.amount))
                .where(Payment.status == "completed")
            )
            total_revenue = payment_result.scalar() or 0.0
            
            return {
                "nodes": {
                    "total": node_stats[0] or 0,
                    "average_reputation": float(node_stats[1] or 0.0),
                    "average_compute_score": float(node_stats[2] or 0.0)
                },
                "jobs": {
                    "total": job_stats[0] or 0,
                    "running": job_stats[1] or 0,
                    "completed": job_stats[2] or 0,
                    "failed": job_stats[3] or 0
                },
                "revenue": {
                    "total": float(total_revenue)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            # Return default structure even on error
            return {
                "nodes": {
                    "total": 0,
                    "average_reputation": 0.0,
                    "average_compute_score": 0.0
                },
                "jobs": {
                    "total": 0,
                    "running": 0,
                    "completed": 0,
                    "failed": 0
                },
                "revenue": {
                    "total": 0.0
                },
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_node_metrics(self, node_id: str) -> Optional[Dict]:
        """Get metrics for a specific node"""
        try:
            node = await self.node_registry.get_node(node_id)
            if not node:
                return None
            
            # Get job statistics for this node
            job_result = await self.db.execute(
                select(
                    func.count(Job.id),
                    func.sum(func.case((Job.status == "completed", 1), else_=0)),
                    func.sum(func.case((Job.status == "failed", 1), else_=0)),
                    func.sum(Job.cost)
                )
                .where(Job.assigned_node == node_id)
            )
            job_stats = job_result.first()
            
            # Get payment statistics
            payment_result = await self.db.execute(
                select(func.sum(Payment.amount))
                .where(Payment.node_id == node_id, Payment.status == "completed")
            )
            total_earnings = payment_result.scalar() or 0.0
            
            return {
                "node_id": node.node_id,
                "status": node.status,
                "gpu_memory": node.gpu_memory,
                "compute_score": node.compute_score,
                "reputation": node.reputation,
                "last_heartbeat": node.last_heartbeat.isoformat() if node.last_heartbeat else None,
                "jobs": {
                    "total": job_stats[0] or 0,
                    "completed": job_stats[1] or 0,
                    "failed": job_stats[2] or 0
                },
                "earnings": float(total_earnings),
                "total_cost": float(job_stats[3] or 0.0)
            }
        except Exception as e:
            logger.error(f"Error getting node metrics {node_id}: {e}")
            return None
    
    async def get_job_metrics(self, job_id: str) -> Optional[Dict]:
        """Get metrics for a specific job"""
        try:
            result = await self.db.execute(
                select(Job).where(Job.job_id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                return None
            
            # Get task statistics
            task_result = await self.db.execute(
                select(
                    func.count(Task.id),
                    func.sum(func.case((Task.status == "completed", 1), else_=0)),
                    func.sum(func.case((Task.status == "failed", 1), else_=0))
                )
                .where(Task.job_id == job_id)
            )
            task_stats = task_result.first()
            
            duration = None
            if job.started_at and job.completed_at:
                duration = (job.completed_at - job.started_at).total_seconds()
            elif job.started_at:
                duration = (datetime.utcnow() - job.started_at).total_seconds()
            
            return {
                "job_id": job.job_id,
                "status": job.status,
                "model": job.model,
                "budget": job.budget,
                "cost": job.cost,
                "assigned_node": job.assigned_node,
                "duration_seconds": duration,
                "tasks": {
                    "total": task_stats[0] or 0,
                    "completed": task_stats[1] or 0,
                    "failed": task_stats[2] or 0
                },
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            }
        except Exception as e:
            logger.error(f"Error getting job metrics {job_id}: {e}")
            return None
    
    async def health_check(self) -> Dict:
        """System health check"""
        try:
            active_nodes = await self.node_registry.get_active_nodes()
            stats = await self.get_system_stats()
            
            health_status = "healthy"
            issues = []
            
            if len(active_nodes) == 0:
                health_status = "degraded"
                issues.append("No active nodes available")
            
            if stats.get("nodes", {}).get("average_reputation", 1.0) < 0.3:
                health_status = "degraded"
                issues.append("Low average node reputation")
            
            return {
                "status": health_status,
                "active_nodes": len(active_nodes),
                "issues": issues,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

