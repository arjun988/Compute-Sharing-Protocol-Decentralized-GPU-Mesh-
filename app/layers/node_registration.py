"""
Layer 1: Node Registration
Handles node registration, heartbeat, and status management
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models import Node
import uuid
import logging

logger = logging.getLogger(__name__)


class NodeRegistry:
    """Node registration and management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.heartbeat_timeout = timedelta(minutes=5)
    
    async def register_node(
        self,
        node_id: str,
        host: str,
        port: int,
        gpu_memory: int = 0,
        compute_score: float = 0.0,
        metadata: Optional[Dict] = None
    ) -> Node:
        """Register a new node"""
        try:
            # Check if node already exists
            result = await self.db.execute(
                select(Node).where(Node.node_id == node_id)
            )
            existing_node = result.scalar_one_or_none()
            
            if existing_node:
                # Update existing node
                existing_node.host = host
                existing_node.port = port
                existing_node.gpu_memory = gpu_memory
                existing_node.compute_score = compute_score
                existing_node.status = "active"
                existing_node.last_heartbeat = datetime.utcnow()
                if metadata:
                    existing_node.meta_data = metadata
                await self.db.commit()
                await self.db.refresh(existing_node)
                logger.info(f"Node {node_id} updated")
                return existing_node
            
            # Create new node
            node = Node(
                node_id=node_id,
                host=host,
                port=port,
                gpu_memory=gpu_memory,
                compute_score=compute_score,
                reputation=0.5,
                status="active",
                last_heartbeat=datetime.utcnow(),
                meta_data=metadata or {}
            )
            self.db.add(node)
            await self.db.commit()
            await self.db.refresh(node)
            logger.info(f"Node {node_id} registered")
            return node
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error registering node {node_id}: {e}")
            raise
    
    async def update_heartbeat(self, node_id: str) -> bool:
        """Update node heartbeat"""
        try:
            result = await self.db.execute(
                update(Node)
                .where(Node.node_id == node_id)
                .values(
                    last_heartbeat=datetime.utcnow(),
                    status="active"
                )
            )
            await self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating heartbeat for {node_id}: {e}")
            return False
    
    async def get_active_nodes(self) -> List[Node]:
        """Get all active nodes"""
        try:
            cutoff_time = datetime.utcnow() - self.heartbeat_timeout
            result = await self.db.execute(
                select(Node).where(
                    Node.status == "active",
                    Node.last_heartbeat >= cutoff_time
                )
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting active nodes: {e}")
            return []
    
    async def get_node(self, node_id: str) -> Optional[Node]:
        """Get node by ID"""
        try:
            result = await self.db.execute(
                select(Node).where(Node.node_id == node_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting node {node_id}: {e}")
            return None
    
    async def update_node_status(self, node_id: str, status: str) -> bool:
        """Update node status"""
        try:
            result = await self.db.execute(
                update(Node)
                .where(Node.node_id == node_id)
                .values(status=status)
            )
            await self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating node status {node_id}: {e}")
            return False
    
    async def get_best_nodes(self, min_gpu_memory: int = 0, limit: int = 10) -> List[Node]:
        """Get best available nodes sorted by score"""
        try:
            cutoff_time = datetime.utcnow() - self.heartbeat_timeout
            result = await self.db.execute(
                select(Node)
                .where(
                    Node.status == "active",
                    Node.last_heartbeat >= cutoff_time,
                    Node.gpu_memory >= min_gpu_memory
                )
                .order_by(Node.compute_score.desc(), Node.reputation.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting best nodes: {e}")
            return []
    
    async def cleanup_inactive_nodes(self) -> int:
        """Mark inactive nodes as offline"""
        try:
            cutoff_time = datetime.utcnow() - self.heartbeat_timeout
            result = await self.db.execute(
                update(Node)
                .where(
                    Node.status == "active",
                    Node.last_heartbeat < cutoff_time
                )
                .values(status="inactive")
            )
            await self.db.commit()
            count = result.rowcount
            if count > 0:
                logger.info(f"Marked {count} nodes as inactive")
            return count
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error cleaning up inactive nodes: {e}")
            return 0

