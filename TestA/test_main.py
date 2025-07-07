# test_main.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db
from models import Base, User
from database import SessionLocal
import os
from datetime import datetime, date

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

# Setup and teardown
@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# Test data
test_user_data = {
    "username": "testdoctor",
    "email": "doctor@test.com",
    "password": "Test1234!",
    "role": "doctor"
}

test_patient_data = {
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1990-01-15",
    "gender": "male",
    "email": "john.doe@test.com",
    "phone": "555-0123",
    "address": "123 Test St, Test City, TC 12345",
    "ssn": "123-45-6789"
}

test_medical_record_data = {
    "patient_id": 1,
    "record_type": "consultation",
    "visit_date": datetime.now().isoformat(),
    "chief_complaint": "Persistent headache for 3 days",
    "diagnosis": "Tension headache",
    "treatment": "Rest, hydration, ibuprofen 400mg as needed",
    "medications": "Ibuprofen 400mg",
    "notes": "Patient advised to return if symptoms worsen"
}

class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_endpoint(self, setup_database):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "Medical Records API is running"
    
    def test_health_endpoint(self, setup_database):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_register_user(self, setup_database):
        response = client.post("/register", json=test_user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert data["role"] == test_user_data["role"]
        assert "id" in data
    
    def test_register_duplicate_user(self, setup_database):
        # First registration
        client.post("/register", json=test_user_data)
        
        # Duplicate registration
        response = client.post("/register", json=test_user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_login_success(self, setup_database):
        # Register user first
        client.post("/register", json=test_user_data)
        
        # Login
        response = client.post("/token", data={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, setup_database):
        response = client.post("/token", data={
            "username": "wronguser",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

class TestPatientEndpoints:
    """Test patient-related endpoints"""
    
    @pytest.fixture
    def auth_headers(self, setup_database):
        # Register and login
        client.post("/register", json=test_user_data)
        response = client.post("/token", data={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_create_patient(self, setup_database, auth_headers):
        response = client.post("/patients", json=test_patient_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == test_patient_data["first_name"]
        assert data["last_name"] == test_patient_data["last_name"]
        assert "id" in data
    
    def test_create_patient_unauthorized(self, setup_database):
        response = client.post("/patients", json=test_patient_data)
        assert response.status_code == 401
    
    def test_list_patients(self, setup_database, auth_headers):
        # Create a patient first
        client.post("/patients", json=test_patient_data, headers=auth_headers)
        
        # List patients
        response = client.get("/patients", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_get_patient_by_id(self, setup_database, auth_headers):
        # Create a patient
        create_response = client.post("/patients", json=test_patient_data, headers=auth_headers)
        patient_id = create_response.json()["id"]
        
        # Get patient by ID
        response = client.get(f"/patients/{patient_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == patient_id
        assert data["first_name"] == test_patient_data["first_name"]
    
    def test_get_nonexistent_patient(self, setup_database, auth_headers):
        response = client.get("/patients/99999", headers=auth_headers)
        assert response.status_code == 404
        assert "Patient not found" in response.json()["detail"]

class TestMedicalRecordEndpoints:
    """Test medical record endpoints"""
    
    @pytest.fixture
    def setup_patient_and_auth(self, setup_database):
        # Register and login
        client.post("/register", json=test_user_data)
        response = client.post("/token", data={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a patient
        patient_response = client.post("/patients", json=test_patient_data, headers=headers)
        patient_id = patient_response.json()["id"]
        
        return headers, patient_id
    
    def test_create_medical_record(self, setup_database, setup_patient_and_auth):
        headers, patient_id = setup_patient_and_auth
        record_data = test_medical_record_data.copy()
        record_data["patient_id"] = patient_id
        
        response = client.post("/medical-records", json=record_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["patient_id"] == patient_id
        assert data["diagnosis"] == record_data["diagnosis"]
        assert data["treatment"] == record_data["treatment"]
    
    def test_create_medical_record_invalid_patient(self, setup_database, setup_patient_and_auth):
        headers, _ = setup_patient_and_auth
        record_data = test_medical_record_data.copy()
        record_data["patient_id"] = 99999
        
        response = client.post("/medical-records", json=record_data, headers=headers)
        assert response.status_code == 404
        assert "Patient not found" in response.json()["detail"]
    
    def test_get_patient_medical_records(self, setup_database, setup_patient_and_auth):
        headers, patient_id = setup_patient_and_auth
        
        # Create a medical record
        record_data = test_medical_record_data.copy()
        record_data["patient_id"] = patient_id
        client.post("/medical-records", json=record_data, headers=headers)
        
        # Get patient's medical records
        response = client.get(f"/medical-records/patient/{patient_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["patient_id"] == patient_id

class TestSearchEndpoints:
    """Test semantic search functionality"""
    
    @pytest.fixture
    def setup_search_data(self, setup_database):
        # Register and login
        client.post("/register", json=test_user_data)
        response = client.post("/token", data={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create multiple patients and records
        patients_data = [
            {
                **test_patient_data,
                "first_name": f"Patient{i}",
                "email": f"patient{i}@test.com"
            }
            for i in range(3)
        ]
        
        records_data = [
            {
                "record_type": "consultation",
                "visit_date": datetime.now().isoformat(),
                "chief_complaint": "Severe headache with nausea",
                "diagnosis": "Migraine",
                "treatment": "Sumatriptan prescribed",
                "medications": "Sumatriptan 50mg"
            },
            {
                "record_type": "consultation",
                "visit_date": datetime.now().isoformat(),
                "chief_complaint": "Chest pain and shortness of breath",
                "diagnosis": "Anxiety attack",
                "treatment": "Relaxation techniques, follow-up recommended",
                "medications": "None"
            },
            {
                "record_type": "lab_result",
                "visit_date": datetime.now().isoformat(),
                "chief_complaint": "Routine blood work",
                "diagnosis": "Normal results",
                "treatment": "Continue current medications",
                "medications": "None"
            }
        ]
        
        # Create patients and records
        for i, patient_data in enumerate(patients_data):
            patient_response = client.post("/patients", json=patient_data, headers=headers)
            patient_id = patient_response.json()["id"]
            
            if i < len(records_data):
                record_data = records_data[i].copy()
                record_data["patient_id"] = patient_id
                client.post("/medical-records", json=record_data, headers=headers)
        
        return headers
    
    def test_semantic_search(self, setup_database, setup_search_data):
        headers = setup_search_data
        
        search_query = {
            "query": "headache migraine",
            "top_k": 5,
            "anonymize": False,
            "rerank": True
        }
        
        response = client.post("/search", json=search_query, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check that results contain relevant fields
        first_result = data[0]
        assert "record_id" in first_result
        assert "patient_id" in first_result
        assert "relevance_score" in first_result
        assert "diagnosis" in first_result
    
    def test_semantic_search_anonymized(self, setup_database, setup_search_data):
        headers = setup_search_data
        
        search_query = {
            "query": "chest pain",
            "top_k": 5,
            "anonymize": True,
            "rerank": False
        }
        
        response = client.post("/search", json=search_query, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            first_result = data[0]
            assert first_result["patient_id"].startswith("PATIENT_")
            assert first_result["diagnosis"] == "**REDACTED**"
            assert first_result["treatment"] == "**REDACTED**"

class TestSecurityAndCompliance:
    """Test security and HIPAA compliance features"""
    
    @pytest.fixture
    def admin_auth_headers(self, setup_database):
        # Register admin user
        admin_data = {
            "username": "admin",
            "email": "admin@test.com",
            "password": "Admin1234!",
            "role": "admin"
        }
        client.post("/register", json=admin_data)
        
        response = client.post("/token", data={
            "username": admin_data["username"],
            "password": admin_data["password"]
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_audit_logs_admin_only(self, setup_database, admin_auth_headers):
        response = client.get("/audit-logs", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_audit_logs_non_admin_forbidden(self, setup_database):
        # Register and login as doctor
        client.post("/register", json=test_user_data)
        response = client.post("/token", data={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/audit-logs", headers=headers)
        assert response.status_code == 403
        assert "Only administrators" in response.json()["detail"]
    
    def test_nurse_read_only_access(self, setup_database):
        # Register nurse user
        nurse_data = {
            "username": "nurse",
            "email": "nurse@test.com",
            "password": "Nurse1234!",
            "role": "nurse"
        }
        client.post("/register", json=nurse_data)
        
        response = client.post("/token", data={
            "username": nurse_data["username"],
            "password": nurse_data["password"]
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Nurse should be able to read patients
        response = client.get("/patients", headers=headers)
        assert response.status_code == 200
        
        # Nurse should not be able to create patients
        response = client.post("/patients", json=test_patient_data, headers=headers)
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]

# test_security.py
import pytest
from security import SecurityManager
from audit import AuditLogger
from datetime import datetime, timedelta

class TestSecurityManager:
    """Test security manager functionality"""
    
    @pytest.fixture
    def security_manager(self):
        return SecurityManager()
    
    def test_encrypt_decrypt_data(self, security_manager):
        plaintext = "Sensitive medical information"
        
        # Encrypt
        encrypted = security_manager.encrypt_data(plaintext)
        assert encrypted != plaintext
        assert isinstance(encrypted, str)
        
        # Decrypt
        decrypted = security_manager.decrypt_data(encrypted)
        assert decrypted == plaintext
    
    def test_encrypt_decrypt_empty_data(self, security_manager):
        assert security_manager.encrypt_data("") is None
        assert security_manager.decrypt_data("") is None
    
    def test_hash_data(self, security_manager):
        data = "Patient SSN: 123-45-6789"
        
        hash1 = security_manager.hash_data(data)
        hash2 = security_manager.hash_data(data)
        
        # Same input should produce same hash
        assert hash1 == hash2
        
        # Hash should be different from input
        assert hash1 != data
        
        # Different input should produce different hash
        hash3 = security_manager.hash_data("Different data")
        assert hash3 != hash1
    
    def test_anonymize_patient_data(self, security_manager):
        patient_data = {
            "patient_id": 123,
            "first_name": "John",
            "last_name": "Doe",
            "ssn": "123-45-6789",
            "email": "john.doe@example.com",
            "phone": "555-0123",
            "address": "123 Main St",
            "date_of_birth": "1990-01-15"
        }
        
        anonymized = security_manager.anonymize_patient_data(patient_data)
        
        assert anonymized["patient_id"] == "PATIENT_000123"
        assert anonymized["first_name"] == "REDACTED_FIRST_NAME"
        assert anonymized["last_name"] == "REDACTED_LAST_NAME"
        assert anonymized["ssn"] == "XXX-XX-6789"
        assert anonymized["email"].startswith("jo***@")
        assert anonymized["phone"] == "REDACTED"
        assert anonymized["address"] == "REDACTED"
        assert anonymized["date_of_birth"] == "1990-01-15"  # DOB not anonymized
    
    def test_validate_access_request(self, security_manager):
        # Admin should have full access
        assert security_manager.validate_access_request("admin", "patients", "read") is True
        assert security_manager.validate_access_request("admin", "anything", "delete") is True
        
        # Doctor should have specific access
        assert security_manager.validate_access_request("doctor", "patients", "read") is True
        assert security_manager.validate_access_request("doctor", "patients", "write") is True
        assert security_manager.validate_access_request("doctor", "patients", "delete") is False
        
        # Nurse should have read-only access
        assert security_manager.validate_access_request("nurse", "patients", "read") is True
        assert security_manager.validate_access_request("nurse", "patients", "write") is False
        assert security_manager.validate_access_request("nurse", "medical_records", "read") is True
        
        # Invalid role should have no access
        assert security_manager.validate_access_request("invalid_role", "patients", "read") is False

if __name__ == "__main__":
    pytest.main(["-v"])