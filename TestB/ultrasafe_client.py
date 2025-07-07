# ultrasafe_client.py
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from config import ULTRASAFE_API_KEY, ULTRASAFE_BASE_URL, create_api_session, logger

class UltraSafeAPIClient:
    def __init__(self, api_key: str = ULTRASAFE_API_KEY):
        self.api_key = api_key
        self.base_url = ULTRASAFE_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.session = create_api_session()
        
    async def search_conditions(self, symptoms: List[str], 
                              age: Optional[int] = None,
                              gender: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for medical conditions based on symptoms"""
        endpoint = f"{self.base_url}/conditions/search"
        
        payload = {
            "symptoms": symptoms,
            "filters": {}
        }
        
        if age:
            payload["filters"]["age"] = age
        if gender:
            payload["filters"]["gender"] = gender
            
        try:
            response = self.session.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json().get("conditions", [])
        except Exception as e:
            logger.error(f"Error searching conditions: {e}")
            return []
    
    async def get_condition_details(self, condition_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific condition"""
        endpoint = f"{self.base_url}/conditions/{condition_id}"
        
        try:
            response = self.session.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting condition details: {e}")
            return {}
    
    async def check_drug_interactions(self, medications: List[str]) -> Dict[str, Any]:
        """Check for drug interactions"""
        endpoint = f"{self.base_url}/medications/interactions"
        
        payload = {
            "medications": medications
        }
        
        try:
            response = self.session.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error checking drug interactions: {e}")
            return {"interactions": [], "severity": "unknown"}
    
    async def get_symptom_details(self, symptom_name: str) -> Dict[str, Any]:
        """Get detailed information about a symptom"""
        endpoint = f"{self.base_url}/symptoms/search"
        
        payload = {
            "query": symptom_name
        }
        
        try:
            response = self.session.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            symptoms = response.json().get("symptoms", [])
            return symptoms[0] if symptoms else {}
        except Exception as e:
            logger.error(f"Error getting symptom details: {e}")
            return {}
    
    async def find_healthcare_providers(self, specialty: str, 
                                      location: Optional[str] = None,
                                      insurance: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find healthcare providers"""
        endpoint = f"{self.base_url}/providers/search"
        
        payload = {
            "specialty": specialty,
            "filters": {}
        }
        
        if location:
            payload["filters"]["location"] = location
        if insurance:
            payload["filters"]["insurance"] = insurance
            
        try:
            response = self.session.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json().get("providers", [])
        except Exception as e:
            logger.error(f"Error finding providers: {e}")
            return []
    
    async def get_procedure_info(self, procedure_name: str) -> Dict[str, Any]:
        """Get information about medical procedures"""
        endpoint = f"{self.base_url}/procedures/search"
        
        payload = {
            "query": procedure_name
        }
        
        try:
            response = self.session.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            procedures = response.json().get("procedures", [])
            return procedures[0] if procedures else {}
        except Exception as e:
            logger.error(f"Error getting procedure info: {e}")
            return {}