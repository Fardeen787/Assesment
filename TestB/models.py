# models.py
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Literal, Any
from datetime import datetime
from enum import Enum

class Severity(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class Symptom(BaseModel):
    name: str
    description: str
    duration: Optional[str] = None
    severity: Severity
    location: Optional[str] = None
    onset: Optional[str] = None
    triggers: List[str] = Field(default_factory=list)
    ultrasafe_id: Optional[str] = None  # UltraSafe symptom ID
    
class PatientInfo(BaseModel):
    age: int
    gender: Literal["male", "female", "other"]
    medical_history: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    insurance: Optional[str] = None
    
class MedicalCondition(BaseModel):
    name: str
    icd_code: Optional[str] = None
    description: str
    symptoms: List[str]
    risk_factors: List[str] = Field(default_factory=list)
    urgency: Severity
    prevalence: Optional[float] = None
    ultrasafe_id: Optional[str] = None  # UltraSafe condition ID
    treatment_options: List[str] = Field(default_factory=list)
    
class DrugInteraction(BaseModel):
    drug1: str
    drug2: str
    severity: Severity
    description: str
    recommendations: List[str]
    
class HealthcareProvider(BaseModel):
    name: str
    specialty: str
    location: str
    phone: Optional[str] = None
    accepts_insurance: List[str] = Field(default_factory=list)
    rating: Optional[float] = None
    ultrasafe_id: Optional[str] = None
    
class Diagnosis(BaseModel):
    condition: MedicalCondition
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    supporting_symptoms: List[str]
    missing_symptoms: List[str]
    differential_diagnoses: List[str] = Field(default_factory=list)
    recommended_tests: List[str] = Field(default_factory=list)
    
class Recommendation(BaseModel):
    action: str
    urgency: Severity
    reasoning: str
    next_steps: List[str]
    warnings: List[str] = Field(default_factory=list)
    providers: List[HealthcareProvider] = Field(default_factory=list)
    estimated_cost_range: Optional[str] = None
    
class ConsultationState(BaseModel):
    session_id: str
    patient_info: Optional[PatientInfo] = None
    symptoms: List[Symptom] = Field(default_factory=list)
    diagnoses: List[Diagnosis] = Field(default_factory=list)
    recommendations: List[Recommendation] = Field(default_factory=list)
    drug_interactions: List[DrugInteraction] = Field(default_factory=list)
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    current_step: str = "initial"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    api_calls_made: List[str] = Field(default_factory=list)