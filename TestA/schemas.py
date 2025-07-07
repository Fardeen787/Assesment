from pydantic import BaseModel, EmailStr, Field, validator
from datetime import date, datetime
from typing import Optional, List, Dict, Any

# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    role: str = Field(..., pattern="^(admin|doctor|nurse)$")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Patient schemas
class PatientBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: date
    gender: str = Field(..., pattern="^(male|female|other)$")
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None

class PatientCreate(PatientBase):
    ssn: Optional[str] = Field(None, pattern="^\\d{3}-\\d{2}-\\d{4}$")

class PatientResponse(PatientBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Medical Record schemas
class MedicalRecordBase(BaseModel):
    patient_id: int
    record_type: str = Field(..., min_length=1, max_length=50)
    visit_date: datetime
    chief_complaint: Optional[str] = None
    medications: Optional[str] = None

class MedicalRecordCreate(MedicalRecordBase):
    diagnosis: str
    treatment: str
    notes: Optional[str] = None

class MedicalRecordResponse(MedicalRecordBase):
    id: int
    diagnosis: Optional[str] = None  # Will be decrypted for response
    treatment: Optional[str] = None  # Will be decrypted for response
    notes: Optional[str] = None  # Will be decrypted for response
    created_at: datetime
    
    class Config:
        from_attributes = True

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Search schemas
class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(10, ge=1, le=100)
    filters: Optional[Dict[str, Any]] = None
    anonymize: bool = True
    rerank: bool = True

class SearchResult(BaseModel):
    record_id: int
    patient_id: str  # Can be anonymized
    relevance_score: float
    chief_complaint: Optional[str]
    diagnosis: str
    treatment: str
    visit_date: datetime

# Audit schemas
class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    resource_type: str
    resource_id: Optional[int]
    ip_address: Optional[str]
    timestamp: datetime
    additional_data: Optional[str]
    
    class Config:
        from_attributes = True
