from cryptography.fernet import Fernet
from typing import List, Dict, Any
import os
import base64
import hashlib
import json
from datetime import datetime
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class SecurityManager:
    """
    Handles encryption, decryption, and security-related operations
    for HIPAA compliance
    """
    
    def __init__(self):
        # Get or generate encryption key
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            # Generate a new key if not provided
            encryption_key = Fernet.generate_key().decode()
            logger.warning("No encryption key found in environment. Generated new key.")
        
        self.cipher_suite = Fernet(encryption_key.encode())
        
        # Initialize audit settings
        self.enable_field_level_encryption = True
        self.enable_audit_trail = True
    
    def encrypt_data(self, plaintext: str) -> str:
        """
        Encrypt sensitive data using Fernet symmetric encryption
        """
        if not plaintext:
            return None
        
        try:
            # Encode to bytes and encrypt
            encrypted_bytes = self.cipher_suite.encrypt(plaintext.encode('utf-8'))
            
            # Return base64 encoded string
            return base64.b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise
    
    def decrypt_data(self, ciphertext: str) -> str:
        """
        Decrypt encrypted data
        """
        if not ciphertext:
            return None
        
        try:
            # Decode from base64 and decrypt
            encrypted_bytes = base64.b64decode(ciphertext.encode('utf-8'))
            decrypted_bytes = self.cipher_suite.decrypt(encrypted_bytes)
            
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise
    
    def hash_data(self, data: str) -> str:
        """
        Create a one-way hash of data for comparison without storing plaintext
        """
        if not data:
            return None
        
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def anonymize_patient_data(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymize patient data for research or reporting purposes
        """
        anonymized = patient_data.copy()
        
        # Fields to anonymize
        sensitive_fields = ['ssn', 'first_name', 'last_name', 'email', 'phone', 'address']
        
        for field in sensitive_fields:
            if field in anonymized:
                if field in ['first_name', 'last_name']:
                    # Replace with generic identifier
                    anonymized[field] = f"REDACTED_{field.upper()}"
                elif field == 'ssn':
                    # Show only last 4 digits
                    anonymized[field] = f"XXX-XX-{anonymized[field][-4:]}" if anonymized[field] else None
                elif field == 'email':
                    # Mask email
                    if anonymized[field]:
                        parts = anonymized[field].split('@')
                        anonymized[field] = f"{parts[0][:2]}***@{parts[1]}" if len(parts) == 2 else "REDACTED"
                else:
                    anonymized[field] = "REDACTED"
        
        # Replace patient ID with anonymous identifier
        if 'patient_id' in anonymized:
            anonymized['patient_id'] = f"PATIENT_{int(anonymized['patient_id']):06d}"
        
        return anonymized
    
    def validate_access_request(self, user_role: str, resource: str, action: str) -> bool:
        """
        Validate if a user role can perform an action on a resource
        """
        # Define role-based access control matrix
        access_matrix = {
            "admin": {
                "*": ["*"]  # Full access
            },
            "doctor": {
                "patients": ["read", "write"],
                "medical_records": ["read", "write"],
                "audit_logs": ["read_own"]
            },
            "nurse": {
                "patients": ["read"],
                "medical_records": ["read"],
                "audit_logs": ["read_own"]
            }
        }
        
        # Check access
        if user_role not in access_matrix:
            return False
        
        role_permissions = access_matrix[user_role]
        
        # Check for wildcard permissions
        if "*" in role_permissions and "*" in role_permissions["*"]:
            return True
        
        # Check specific resource permissions
        if resource in role_permissions:
            return action in role_permissions[resource] or "*" in role_permissions[resource]
        
        return False
    
    def rerank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Rerank search results based on clinical relevance and access controls
        """
        # For now, return results as is
        # In production, implement proper reranking logic
        return results
