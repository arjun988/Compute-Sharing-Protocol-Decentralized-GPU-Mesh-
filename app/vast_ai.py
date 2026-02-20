"""
Vast.ai API Integration
Handles GPU rental from Vast.ai
"""
import requests
from typing import Dict, List, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class VastAIClient:
    """Vast.ai API client"""
    
    def __init__(self):
        self.api_key = settings.vast_api_key
        self.api_url = settings.vast_api_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}" if self.api_key else None
        }
    
    def search_offers(
        self,
        min_gpu_memory: int = 0,
        max_price: Optional[float] = None,
        gpu_name: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Search for available GPU offers"""
        if not self.api_key:
            logger.warning("Vast.ai API key not configured, returning empty results")
            return []
        
        try:
            params = {
                "type": "on-demand",
                "order": "price",
                "limit": limit
            }
            
            if min_gpu_memory:
                params["min_gpu_memory"] = min_gpu_memory
            
            if max_price:
                params["max_price"] = max_price
            
            if gpu_name:
                params["gpu_name"] = gpu_name
            
            response = requests.get(
                f"{self.api_url}/offers",
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("offers", [])
            else:
                logger.error(f"Vast.ai API error: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error searching Vast.ai offers: {e}")
            return []
    
    def get_cheapest_offer(
        self,
        min_gpu_memory: int = 0,
        max_price: Optional[float] = None
    ) -> Optional[Dict]:
        """Get cheapest available GPU offer"""
        offers = self.search_offers(
            min_gpu_memory=min_gpu_memory,
            max_price=max_price,
            limit=1
        )
        
        if offers:
            return offers[0]
        return None
    
    def create_instance(self, offer_id: str, config: Dict) -> Optional[Dict]:
        """Create a GPU instance from an offer"""
        if not self.api_key:
            logger.warning("Vast.ai API key not configured")
            return None
        
        try:
            payload = {
                "offer_id": offer_id,
                **config
            }
            
            response = requests.post(
                f"{self.api_url}/instances",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error creating instance: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating Vast.ai instance: {e}")
            return None
    
    def get_instance(self, instance_id: str) -> Optional[Dict]:
        """Get instance details"""
        if not self.api_key:
            return None
        
        try:
            response = requests.get(
                f"{self.api_url}/instances/{instance_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error getting instance {instance_id}: {e}")
            return None
    
    def terminate_instance(self, instance_id: str) -> bool:
        """Terminate an instance"""
        if not self.api_key:
            return False
        
        try:
            response = requests.delete(
                f"{self.api_url}/instances/{instance_id}",
                headers=self.headers,
                timeout=10
            )
            
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error terminating instance {instance_id}: {e}")
            return False

