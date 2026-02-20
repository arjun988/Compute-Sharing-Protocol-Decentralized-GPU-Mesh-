"""
Pydantic schemas for API requests/responses
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


class NodeRegisterRequest(BaseModel):
    node_id: str
    host: str
    port: int
    gpu_memory: int = 0
    compute_score: float = 0.0
    metadata: Optional[Dict] = None


class NodeResponse(BaseModel):
    id: str
    node_id: str
    host: str
    port: int
    gpu_memory: int
    compute_score: float
    reputation: float
    status: str
    registered_at: datetime
    last_heartbeat: datetime
    
    class Config:
        from_attributes = True


class FinetuneRequest(BaseModel):
    model: str = Field(..., description="Model name (e.g., llama-3-8b)")
    dataset: Optional[str] = Field(None, description="Dataset path or name")
    max_budget: Optional[float] = Field(None, description="Maximum budget in USD")
    speed: str = Field("balanced", description="Speed preference: fast, balanced, cheap")
    user_id: str = Field(default="default_user", description="User ID")
    metadata: Optional[Dict] = None


class JobResponse(BaseModel):
    id: str
    job_id: str
    user_id: str
    job_type: str
    status: str
    model: str
    dataset: Optional[str]
    budget: Optional[float]
    speed: str
    assigned_node: Optional[str]
    cost: float
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class SystemStatsResponse(BaseModel):
    nodes: Dict
    jobs: Dict
    revenue: Dict
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    active_nodes: int
    issues: List[str]
    timestamp: str

