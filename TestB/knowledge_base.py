# knowledge_base.py
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import json
import asyncio
from typing import List, Dict, Any, Optional
import numpy as np

from models import PatientInfo, MedicalCondition, Symptom, Severity
from ultrasafe_client import UltraSafeAPIClient

class EnhancedMedicalKnowledgeBase:
    def __init__(self, collection_name: str = "medical_knowledge"):
        self.client = chromadb.PersistentClient(path="./medical_db")
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
        self.ultrasafe_client = UltraSafeAPIClient()
        
    async def search_conditions_hybrid(self, symptoms: List[str], 
                                     patient_info: Optional[PatientInfo] = None,
                                     k: int = 10) -> List[MedicalCondition]:
        """Hybrid search using both local knowledge base and UltraSafe API"""
        # Local search
        local_results = self._search_local_conditions(symptoms, k=k//2)
        
        # UltraSafe API search
        age = patient_info.age if patient_info else None
        gender = patient_info.gender if patient_info else None
        api_results = await self.ultrasafe_client.search_conditions(symptoms, age, gender)
        
        # Combine and deduplicate results
        conditions = []
        seen_names = set()
        
        # Process API results first (more current)
        for result in api_results[:k//2]:
            condition = MedicalCondition(
                name=result.get("name", ""),
                icd_code=result.get("icd_code"),
                description=result.get("description", ""),
                symptoms=result.get("symptoms", []),
                risk_factors=result.get("risk_factors", []),
                urgency=self._map_urgency(result.get("severity", "moderate")),
                prevalence=result.get("prevalence"),
                ultrasafe_id=result.get("id"),
                treatment_options=result.get("treatment_options", [])
            )
            conditions.append(condition)
            seen_names.add(condition.name.lower())
            
        # Add local results if not duplicates
        for result in local_results:
            if result.name.lower() not in seen_names:
                conditions.append(result)
                
        return conditions
    
    def _search_local_conditions(self, symptoms: List[str], k: int = 5) -> List[MedicalCondition]:
        """Search local knowledge base for conditions"""
        query = " ".join(symptoms)
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            include=['documents', 'metadatas', 'distances']
        )
        
        conditions = []
        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i]
            condition_tags = json.loads(metadata.get('condition_tags', '[]'))
            symptom_tags = json.loads(metadata.get('symptom_tags', '[]'))
            
            if condition_tags:
                condition = MedicalCondition(
                    name=condition_tags[0],
                    description=results['documents'][0][i][:200],
                    symptoms=symptom_tags,
                    risk_factors=[],
                    urgency=Severity.MODERATE
                )
                conditions.append(condition)
                
        return conditions
    
    def _map_urgency(self, severity: str) -> Severity:
        """Map API severity to internal severity enum"""
        mapping = {
            "mild": Severity.LOW,
            "moderate": Severity.MODERATE,
            "severe": Severity.HIGH,
            "critical": Severity.CRITICAL
        }
        return mapping.get(severity.lower(), Severity.MODERATE)
    
    async def verify_symptoms(self, symptoms: List[Symptom]) -> List[Symptom]:
        """Verify and enhance symptoms with UltraSafe data"""
        verified_symptoms = []
        
        for symptom in symptoms:
            details = await self.ultrasafe_client.get_symptom_details(symptom.name)
            if details:
                symptom.ultrasafe_id = details.get("id")
                symptom.description = details.get("description", symptom.description)
                if not symptom.triggers and details.get("common_triggers"):
                    symptom.triggers = details.get("common_triggers", [])
                    
            verified_symptoms.append(symptom)
            
        return verified_symptoms