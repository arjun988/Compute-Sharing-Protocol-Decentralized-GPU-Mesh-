"""
Layer 4: Payment and Reputation
Handles payment processing and reputation management
"""
import asyncio
from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.models import Payment, ReputationHistory, Node, Job
import uuid
import logging

logger = logging.getLogger(__name__)


class PaymentManager:
    """Payment processing"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_payment(
        self,
        job_id: str,
        node_id: str,
        user_id: str,
        amount: float,
        metadata: Optional[Dict] = None
    ) -> Payment:
        """Create a payment transaction"""
        try:
            payment = Payment(
                transaction_id=f"tx_{uuid.uuid4().hex[:12]}",
                job_id=job_id,
                node_id=node_id,
                user_id=user_id,
                amount=amount,
                status="pending",
                meta_data=metadata or {}
            )
            self.db.add(payment)
            await self.db.commit()
            await self.db.refresh(payment)
            logger.info(f"Payment {payment.transaction_id} created for job {job_id}")
            return payment
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating payment: {e}")
            raise
    
    async def complete_payment(self, transaction_id: str) -> bool:
        """Complete a payment transaction"""
        try:
            result = await self.db.execute(
                update(Payment)
                .where(Payment.transaction_id == transaction_id)
                .values(
                    status="completed",
                    completed_at=datetime.utcnow()
                )
            )
            await self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error completing payment {transaction_id}: {e}")
            return False
    
    async def get_job_cost(self, job_id: str) -> float:
        """Get total cost for a job"""
        try:
            result = await self.db.execute(
                select(func.sum(Payment.amount))
                .where(Payment.job_id == job_id, Payment.status == "completed")
            )
            total = result.scalar() or 0.0
            return float(total)
        except Exception as e:
            logger.error(f"Error getting job cost {job_id}: {e}")
            return 0.0


class ReputationManager:
    """Reputation management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def update_reputation(
        self,
        node_id: str,
        change: float,
        reason: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> bool:
        """Update node reputation"""
        try:
            # Get current node
            result = await self.db.execute(
                select(Node).where(Node.node_id == node_id)
            )
            node = result.scalar_one_or_none()
            
            if not node:
                logger.warning(f"Node {node_id} not found")
                return False
            
            # Calculate new reputation (clamped between 0 and 1)
            new_reputation = max(0.0, min(1.0, node.reputation + change))
            
            # Update node reputation
            await self.db.execute(
                update(Node)
                .where(Node.node_id == node_id)
                .values(reputation=new_reputation)
            )
            
            # Record history
            history = ReputationHistory(
                node_id=node_id,
                job_id=job_id,
                change=change,
                reason=reason
            )
            self.db.add(history)
            
            await self.db.commit()
            logger.info(f"Node {node_id} reputation updated: {node.reputation} -> {new_reputation} ({reason})")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating reputation for {node_id}: {e}")
            return False
    
    async def reward_node(self, node_id: str, job_id: str, success: bool) -> bool:
        """Reward or penalize node based on job outcome"""
        if success:
            # Reward successful completion
            return await self.update_reputation(
                node_id,
                change=0.01,
                reason="job_completed_successfully",
                job_id=job_id
            )
        else:
            # Penalize failure
            return await self.update_reputation(
                node_id,
                change=-0.05,
                reason="job_failed",
                job_id=job_id
            )
    
    async def get_reputation_history(self, node_id: str, limit: int = 50) -> list:
        """Get reputation history for a node"""
        try:
            result = await self.db.execute(
                select(ReputationHistory)
                .where(ReputationHistory.node_id == node_id)
                .order_by(ReputationHistory.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting reputation history for {node_id}: {e}")
            return []

