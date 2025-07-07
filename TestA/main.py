# main.py
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from jose import jwt
import bcrypt
from contextlib import asynccontextmanager
import logging
import os
from dotenv import load_dotenv

# Local imports
from database import get_db, engine, Base
from models import User, Patient, MedicalRecord, AuditLog, AccessPermission
from schemas import (
    UserCreate, UserResponse, PatientCreate, PatientResponse,
    MedicalRecordCreate, MedicalRecordResponse, Token,
    SearchQuery, SearchResult, AuditLogResponse
)
from vector_store import VectorStore
from security import SecurityManager
from audit import AuditLogger

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Initialize components
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
vector_store = VectorStore()
security_manager = SecurityManager()
audit_logger = AuditLogger()

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Medical Records API")
    Base.metadata.create_all(bind=engine)
    vector_store.initialize()
    yield
    # Shutdown
    logger.info("Shutting down Medical Records API")

# Create FastAPI app
app = FastAPI(
    title="Medical Records API",
    description="HIPAA-compliant medical records management system with semantic search",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.utcnow()
    response = await call_next(request)
    
    # Log request details
    audit_logger.log_api_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=(datetime.utcnow() - start_time).total_seconds()
    )
    
    return response

# Authentication functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user

def check_permission(user: User, resource: str, action: str, db: Session):
    """Check if user has permission for specific action on resource"""
    permission = db.query(AccessPermission).filter(
        AccessPermission.user_id == user.id,
        AccessPermission.resource == resource,
        AccessPermission.action == action
    ).first()
    
    if not permission:
        # Check for wildcard permissions
        permission = db.query(AccessPermission).filter(
            AccessPermission.user_id == user.id,
            AccessPermission.resource == resource,
            AccessPermission.action == "*"
        ).first()
    
    return permission is not None

# API Endpoints

@app.get("/", tags=["Health"])
def read_root():
    return {"message": "Medical Records API is running", "version": "1.0.0"}

@app.post("/register", response_model=UserResponse, tags=["Authentication"])
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with encrypted password"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Hash password
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    
    # Create user
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password.decode('utf-8'),
        role=user.role,
        is_active=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Add default permissions based on role
    if user.role == "doctor":
        permissions = [
            ("patients", "read"),
            ("patients", "write"),
            ("medical_records", "read"),
            ("medical_records", "write")
        ]
    elif user.role == "nurse":
        permissions = [
            ("patients", "read"),
            ("medical_records", "read")
        ]
    else:  # admin
        permissions = [
            ("*", "*")  # Full access
        ]
    
    for resource, action in permissions:
        permission = AccessPermission(
            user_id=db_user.id,
            resource=resource,
            action=action
        )
        db.add(permission)
    
    db.commit()
    
    # Log registration
    audit_logger.log_user_action(db, db_user.id, "register", "user", db_user.id)
    
    return db_user

@app.post("/token", response_model=Token, tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login endpoint that returns JWT token"""
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not bcrypt.checkpw(form_data.password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Create token
    access_token = create_access_token(data={"sub": user.username})
    
    # Log login
    audit_logger.log_user_action(db, user.id, "login", "auth", user.id)
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/patients", response_model=PatientResponse, tags=["Patients"])
async def create_patient(
    patient: PatientCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new patient record"""
    # Check permission
    if not check_permission(current_user, "patients", "write", db):
        raise HTTPException(status_code=403, detail="Not authorized to create patients")
    
    # Encrypt sensitive data
    encrypted_ssn = security_manager.encrypt_data(patient.ssn) if patient.ssn else None
    
    # Create patient
    db_patient = Patient(
        first_name=patient.first_name,
        last_name=patient.last_name,
        date_of_birth=patient.date_of_birth,
        gender=patient.gender,
        email=patient.email,
        phone=patient.phone,
        address=patient.address,
        ssn_encrypted=encrypted_ssn,
        created_by=current_user.id
    )
    
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    
    # Log action
    audit_logger.log_user_action(db, current_user.id, "create", "patient", db_patient.id)
    
    return db_patient

@app.get("/patients", response_model=List[PatientResponse], tags=["Patients"])
async def list_patients(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all patients with pagination"""
    # Check permission
    if not check_permission(current_user, "patients", "read", db):
        raise HTTPException(status_code=403, detail="Not authorized to view patients")
    
    patients = db.query(Patient).offset(skip).limit(limit).all()
    
    # Log action
    audit_logger.log_user_action(db, current_user.id, "list", "patients", None)
    
    return patients

@app.get("/patients/{patient_id}", response_model=PatientResponse, tags=["Patients"])
async def get_patient(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific patient by ID"""
    # Check permission
    if not check_permission(current_user, "patients", "read", db):
        raise HTTPException(status_code=403, detail="Not authorized to view patients")
    
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Log action
    audit_logger.log_user_action(db, current_user.id, "read", "patient", patient_id)
    
    return patient

@app.post("/medical-records", response_model=MedicalRecordResponse, tags=["Medical Records"])
async def create_medical_record(
    record: MedicalRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new medical record"""
    # Check permission
    if not check_permission(current_user, "medical_records", "write", db):
        raise HTTPException(status_code=403, detail="Not authorized to create medical records")
    
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == record.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Encrypt sensitive data
    encrypted_diagnosis = security_manager.encrypt_data(record.diagnosis)
    encrypted_treatment = security_manager.encrypt_data(record.treatment)
    encrypted_notes = security_manager.encrypt_data(record.notes) if record.notes else None
    
    # Create medical record
    db_record = MedicalRecord(
        patient_id=record.patient_id,
        record_type=record.record_type,
        visit_date=record.visit_date,
        chief_complaint=record.chief_complaint,
        diagnosis_encrypted=encrypted_diagnosis,
        treatment_encrypted=encrypted_treatment,
        medications=record.medications,
        notes_encrypted=encrypted_notes,
        created_by=current_user.id
    )
    
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    # Add to vector store for semantic search
    record_text = f"{record.chief_complaint} {record.diagnosis} {record.treatment}"
    vector_store.add_document(
        doc_id=f"medical_record_{db_record.id}",
        text=record_text,
        metadata={
            "patient_id": record.patient_id,
            "record_id": db_record.id,
            "record_type": record.record_type,
            "visit_date": str(record.visit_date)
        }
    )
    
    # Log action
    audit_logger.log_user_action(db, current_user.id, "create", "medical_record", db_record.id)
    
    # Decrypt for response
    db_record.diagnosis = security_manager.decrypt_data(db_record.diagnosis_encrypted)
    db_record.treatment = security_manager.decrypt_data(db_record.treatment_encrypted)
    if db_record.notes_encrypted:
        db_record.notes = security_manager.decrypt_data(db_record.notes_encrypted)
    
    return db_record

@app.get("/medical-records/patient/{patient_id}", response_model=List[MedicalRecordResponse], tags=["Medical Records"])
async def get_patient_medical_records(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all medical records for a patient"""
    # Check permission
    if not check_permission(current_user, "medical_records", "read", db):
        raise HTTPException(status_code=403, detail="Not authorized to view medical records")
    
    records = db.query(MedicalRecord).filter(MedicalRecord.patient_id == patient_id).all()
    
    # Decrypt sensitive data for response
    for record in records:
        record.diagnosis = security_manager.decrypt_data(record.diagnosis_encrypted)
        record.treatment = security_manager.decrypt_data(record.treatment_encrypted)
        if record.notes_encrypted:
            record.notes = security_manager.decrypt_data(record.notes_encrypted)
    
    # Log action
    audit_logger.log_user_action(db, current_user.id, "read", "medical_records", patient_id)
    
    return records

@app.post("/search", response_model=List[SearchResult], tags=["Search"])
async def semantic_search(
    query: SearchQuery,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform semantic search on medical records"""
    # Check permission
    if not check_permission(current_user, "medical_records", "read", db):
        raise HTTPException(status_code=403, detail="Not authorized to search medical records")
    
    # Perform vector search
    results = vector_store.search(
        query_text=query.query,
        top_k=query.top_k,
        filters=query.filters
    )
    
    # Retrieve and anonymize results
    search_results = []
    for result in results:
        record_id = int(result['metadata']['record_id'])
        record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
        
        if record:
            # Decrypt data
            diagnosis = security_manager.decrypt_data(record.diagnosis_encrypted)
            treatment = security_manager.decrypt_data(record.treatment_encrypted)
            
            # Anonymize if needed
            if query.anonymize:
                patient_id = f"PATIENT_{record.patient_id:06d}"
            else:
                patient_id = str(record.patient_id)
            
            search_results.append(SearchResult(
                record_id=record.id,
                patient_id=patient_id,
                relevance_score=result['score'],
                chief_complaint=record.chief_complaint,
                diagnosis=diagnosis if not query.anonymize else "**REDACTED**",
                treatment=treatment if not query.anonymize else "**REDACTED**",
                visit_date=record.visit_date
            ))
    
    # Apply reranking based on clinical relevance
    if query.rerank:
        search_results = security_manager.rerank_results(search_results, query.query)
    
    # Log search action
    audit_logger.log_user_action(
        db, current_user.id, "search", "medical_records", 
        data={"query": query.query, "anonymized": query.anonymize}
    )
    
    return search_results

@app.get("/audit-logs", response_model=List[AuditLogResponse], tags=["Audit"])
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve audit logs (admin only)"""
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can view audit logs")
    
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    return logs

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "vector_store": vector_store.is_healthy(),
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)