"""
FastAPI main application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.config import settings
from app.database import engine, Base
import logging
import asyncio

logging.basicConfig(level=getattr(logging, settings.log_level))

app = FastAPI(
    title="OpenMesh v0.1",
    description="Decentralized GPU Mesh Compute Sharing Protocol",
    version="0.1.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logging.info("Database initialized successfully!")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1", tags=["api"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "OpenMesh v0.1",
        "description": "Decentralized GPU Mesh Compute Sharing Protocol",
        "version": "0.1.0",
        "status": "running"
    }

