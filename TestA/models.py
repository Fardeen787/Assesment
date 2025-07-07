from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # admin, doctor, nurse
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships with explicit foreign keys
    permissions = relationship("AccessPermission", back_populates="user", foreign_keys="AccessPermission.user_id")
    audit_logs = relationship("AuditLog", back_populates="user")
    created_patients = relationship("Patient", back_populates="creator")
    created_records = relationship("MedicalRecord", back_populates="creator")

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    address = Column(Text)
    ssn_encrypted = Column(String)  # Encrypted SSN
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="created_patients")
    medical_records = relationship("MedicalRecord", back_populates="patient")

class MedicalRecord(Base):
    __tablename__ = "medical_records"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    record_type = Column(String, nullable=False)  # consultation, lab_result, imaging, etc.
    visit_date = Column(DateTime, nullable=False)
    chief_complaint = Column(Text)
    diagnosis_encrypted = Column(Text, nullable=False)  # Encrypted diagnosis
    treatment_encrypted = Column(Text, nullable=False)  # Encrypted treatment
    medications = Column(Text)  # JSON string of medications
    notes_encrypted = Column(Text)  # Encrypted additional notes
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="medical_records")
    creator = relationship("User", back_populates="created_records")

class AccessPermission(Base):
    __tablename__ = "access_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resource = Column(String, nullable=False)  # patients, medical_records, etc.
    action = Column(String, nullable=False)  # read, write, delete, *
    granted_at = Column(DateTime, default=datetime.utcnow)
    granted_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships with explicit foreign_keys
    user = relationship("User", back_populates="permissions", foreign_keys=[user_id])
    # No back_populates for granted_by to avoid circular reference

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)  # create, read, update, delete, search
    resource_type = Column(String, nullable=False)  # patient, medical_record, etc.
    resource_id = Column(Integer)
    ip_address = Column(String)
    user_agent = Column(Text)
    additional_data = Column(Text)  # JSON string for extra details
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
