"""
Layer 3: Task Containerization
Handles Docker container creation and management for task execution
"""
import docker
from typing import Dict, Optional, List
from app.config import settings
import logging
import json

logger = logging.getLogger(__name__)


class ContainerManager:
    """Docker container management"""
    
    def __init__(self):
        try:
            self.client = docker.from_env()
            logger.info("Docker client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None
    
    def create_container(
        self,
        task_id: str,
        job_type: str,
        model: str,
        dataset: Optional[str] = None,
        environment: Optional[Dict] = None,
        volumes: Optional[Dict] = None
    ) -> Optional[str]:
        """Create a Docker container for task execution"""
        if not self.client:
            logger.error("Docker client not available")
            return None
        
        try:
            # Base image based on job type
            if job_type == "finetune":
                image = "python:3.11-slim"
            else:
                image = "python:3.11-slim"
            
            # Environment variables
            env_vars = {
                "TASK_ID": task_id,
                "JOB_TYPE": job_type,
                "MODEL": model,
                "PYTHONUNBUFFERED": "1"
            }
            
            if dataset:
                env_vars["DATASET"] = dataset
            
            if environment:
                env_vars.update(environment)
            
            # Container configuration
            container_config = {
                "image": image,
                "name": f"openmesh_task_{task_id}",
                "environment": env_vars,
                "detach": True,
                "auto_remove": False,
                "network_disabled": False,
                "mem_limit": "4g",  # Limit memory
                "cpu_count": 2,  # Limit CPU
            }
            
            if volumes:
                container_config["volumes"] = volumes
            
            container = self.client.containers.run(**container_config)
            container_id = container.id
            logger.info(f"Container {container_id} created for task {task_id}")
            return container_id
        except Exception as e:
            logger.error(f"Error creating container for task {task_id}: {e}")
            return None
    
    def get_container_status(self, container_id: str) -> Optional[str]:
        """Get container status"""
        if not self.client:
            return None
        
        try:
            container = self.client.containers.get(container_id)
            return container.status
        except docker.errors.NotFound:
            return "not_found"
        except Exception as e:
            logger.error(f"Error getting container status {container_id}: {e}")
            return None
    
    def stop_container(self, container_id: str) -> bool:
        """Stop a container"""
        if not self.client:
            return False
        
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            logger.info(f"Container {container_id} stopped")
            return True
        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error stopping container {container_id}: {e}")
            return False
    
    def remove_container(self, container_id: str) -> bool:
        """Remove a container"""
        if not self.client:
            return False
        
        try:
            container = self.client.containers.get(container_id)
            container.remove()
            logger.info(f"Container {container_id} removed")
            return True
        except docker.errors.NotFound:
            return True  # Already removed
        except Exception as e:
            logger.error(f"Error removing container {container_id}: {e}")
            return False
    
    def get_container_logs(self, container_id: str, tail: int = 100) -> Optional[str]:
        """Get container logs"""
        if not self.client:
            return None
        
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail).decode('utf-8')
            return logs
        except Exception as e:
            logger.error(f"Error getting container logs {container_id}: {e}")
            return None
    
    def list_containers(self, filters: Optional[Dict] = None) -> List[Dict]:
        """List containers"""
        if not self.client:
            return []
        
        try:
            containers = self.client.containers.list(all=True, filters=filters or {})
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "status": c.status,
                    "image": c.image.tags[0] if c.image.tags else "unknown"
                }
                for c in containers
            ]
        except Exception as e:
            logger.error(f"Error listing containers: {e}")
            return []

