"""
Run Celery worker
"""
import sys
from app.tasks import celery_app

if __name__ == "__main__":
    # Windows compatibility: use 'solo' pool
    pool_arg = "--pool=solo" if sys.platform == "win32" else "--pool=prefork"
    
    celery_app.worker_main([
        "worker",
        "--loglevel=info",
        pool_arg,
        "--concurrency=1" if sys.platform == "win32" else "--concurrency=4"
    ])

