"""
Database models
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Node(Base):
    """Node registration model"""
    __tablename__ = "nodes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    node_id = Column(String, unique=True, nullable=False, index=True)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    gpu_memory = Column(Integer, default=0)  # Simulated GPU memory in GB
    compute_score = Column(Float, default=0.0)  # Performance score
    reputation = Column(Float, default=0.5)  # Reputation score (0-1)
    status = Column(String, default="active")  # active, inactive, busy
    registered_at = Column(DateTime, server_default=func.now())
    last_heartbeat = Column(DateTime, server_default=func.now())
    meta_data = Column(JSON, default=dict)


class Job(Base):
    """Job model"""
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(String, nullable=False)
    job_type = Column(String, nullable=False)  # finetune, inference, etc.
    status = Column(String, default="pending")  # pending, running, completed, failed
    model = Column(String, nullable=False)
    dataset = Column(String, nullable=True)
    budget = Column(Float, nullable=True)
    speed = Column(String, default="balanced")  # fast, balanced, cheap
    assigned_node = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cost = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    meta_data = Column(JSON, default=dict)


class Task(Base):
    """Task model"""
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, unique=True, nullable=False, index=True)
    job_id = Column(String, nullable=False, index=True)
    node_id = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, running, completed, failed
    container_id = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # in seconds
    meta_data = Column(JSON, default=dict)


class Payment(Base):
    """Payment transaction model"""
    __tablename__ = "payments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String, unique=True, nullable=False, index=True)
    job_id = Column(String, nullable=False, index=True)
    node_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="pending")  # pending, completed, failed
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    meta_data = Column(JSON, default=dict)


class ReputationHistory(Base):
    """Reputation history model"""
    __tablename__ = "reputation_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    node_id = Column(String, nullable=False, index=True)
    job_id = Column(String, nullable=True)
    change = Column(Float, nullable=False)  # Reputation change amount
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

