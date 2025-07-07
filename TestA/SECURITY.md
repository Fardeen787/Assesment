# Security Documentation - Medical Records API

## Overview

This document outlines the security measures implemented in the Medical Records API to ensure HIPAA compliance and protect sensitive patient health information (PHI).

## HIPAA Compliance Features

### 1. Administrative Safeguards

#### Access Control (§164.308(a)(3))
- **User Authentication**: JWT-based authentication with secure token generation
- **Role-Based Access Control (RBAC)**: Three distinct roles with specific permissions
  - **Admin**: Full system access including audit logs
  - **Doctor**: Read/write access to patients and medical records
  - **Nurse**: Read-only access to patients and medical records
- **Automatic Session Timeout**: 30-minute token expiration
- **User Account Management**: Secure registration with email verification

#### Audit Controls (§164.308(a)(1)(ii)(D))
- **Comprehensive Logging**: All access and modifications logged
- **Audit Trail Components**:
  - User ID and username
  - Action performed (create, read, update, delete, search)
  - Resource type and ID
  - Timestamp
  - IP address (when available)
  - Additional context data
- **Audit Log Protection**: Admin-only access to prevent tampering
- **Search Activity Tracking**: All searches logged with anonymization status

### 2. Physical Safeguards

While this is a software implementation, the following considerations apply:

- **Deployment Security**: Recommendations for secure server deployment
- **Data Center Requirements**: Guidelines for HIPAA-compliant hosting
- **Backup Security**: Encrypted backup procedures

### 3. Technical Safeguards

#### Access Control (§164.312(a))
- **Unique User Identification**: Username/email combination
- **Automatic Logoff**: Token expiration after 30 minutes
- **Encryption and Decryption**: Field-level encryption for PHI

#### Audit Controls (§164.312(b))
- **Hardware and Software Monitoring**: Application-level audit logging
- **Intrusion Detection**: Recommendations for deployment-level monitoring

#### Integrity (§164.312(c))
- **Data Validation**: Input validation on all endpoints
- **Cryptographic Hashing**: Password hashing with bcrypt
- **Database Constraints**: Foreign key relationships and data integrity

#### Transmission Security (§164.312(e))
- **HTTPS Enforcement**: Required for production deployment
- **API Security**: OAuth2 bearer token authentication
- **Encrypted Storage**: Sensitive fields encrypted at rest

## Encryption Implementation

### Field-Level Encryption

**Encrypted Fields**:
- Patient SSN
- Medical diagnosis
- Treatment details
- Clinical notes

**Encryption Method**:
- Algorithm: Fernet (symmetric encryption)
- Key Size: 256-bit
- Implementation: Python cryptography library

**Key Management**:
```python
# Key generation
from cryptography.fernet import Fernet
encryption_key = Fernet.generate_key()

# Key storage (environment variable)
ENCRYPTION_KEY=<base64-encoded-key>
```

### Password Security

**Hashing Algorithm**: bcrypt
- Cost Factor: 12 (default)
- Salt: Automatically generated per password
- Implementation:
```python
import bcrypt
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
```

## Authentication & Authorization

### JWT Token Structure

```json
{
  "sub": "username",
  "exp": 1234567890,
  "iat": 1234567860
}
```

**Token Security**:
- HS256 algorithm
- Secret key rotation recommended
- No sensitive data in payload

### Permission Matrix

| Role    | Patients      | Medical Records | Audit Logs | Search |
|---------|---------------|-----------------|------------|--------|
| Admin   | Read/Write    | Read/Write      | Read       | Yes    |
| Doctor  | Read/Write    | Read/Write      | No         | Yes    |
| Nurse   | Read Only     | Read Only       | No         | Yes    |

### API Endpoint Security

All endpoints except health checks require authentication:
```python
current_user: User = Depends(get_current_user)
```

Permission checking on each request:
```python
if not check_permission(current_user, "resource", "action", db):
    raise HTTPException(status_code=403)
```

## Data Privacy Features

### Anonymization

**Patient Data Anonymization**:
- Names replaced with "REDACTED_FIRST_NAME" / "REDACTED_LAST_NAME"
- SSN shows only last 4 digits: "XXX-XX-6789"
- Email partially masked: "jo***@example.com"
- Phone and address completely redacted
- Patient ID replaced with anonymous identifier

**Search Result Anonymization**:
- Optional anonymization flag
- Diagnosis and treatment redacted when enabled
- Patient identifiers replaced with anonymous IDs

### Data Minimization

- Only necessary fields collected
- Optional fields clearly marked
- No data retention beyond requirements
- Secure deletion procedures

## Security Best Practices

### 1. Development Security

```python
# Never log sensitive data
logger.info(f"User {user_id} accessed patient record")  # Good
logger.info(f"SSN: {ssn}")  # Never do this

# Always validate input
@app.post("/patients")
async def create_patient(patient: PatientCreate):  # Pydantic validation
    # Additional validation as needed
```

### 2. Deployment Security

**Environment Variables**:
```bash
# Production .env file
SECRET_KEY=<strong-random-key>
ENCRYPTION_KEY=<fernet-key>
DATABASE_URL=postgresql://user:pass@host/db
ENVIRONMENT=production
```

**HTTPS Configuration**:
```nginx
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
}
```

### 3. Database Security

**Connection Security**:
```python
# PostgreSQL SSL connection
DATABASE_URL = "postgresql://user:pass@host/db?sslmode=require"
```

**Access Control**:
- Separate database users for application and admin
- Minimal permissions per user
- No direct database access from application

### 4. Monitoring & Incident Response

**Security Monitoring**:
- Failed login attempts tracking
- Unusual access pattern detection
- API rate limit monitoring
- Error rate tracking

**Incident Response Plan**:
1. Detect - Automated alerts for security events
2. Contain - Automatic account lockout on suspicious activity
3. Investigate - Comprehensive audit logs
4. Remediate - Clear procedures for security updates
5. Document - Incident reporting requirements

## Compliance Checklist

### HIPAA Technical Safeguards Compliance

- [x] Access Control (§164.312(a)(1))
  - [x] Unique user identification
  - [x] Automatic logoff
  - [x] Encryption/decryption
- [x] Audit Controls (§164.312(b))
  - [x] Audit logs implementation
  - [x] Log monitoring capability
- [x] Integrity (§164.312(c)(1))
  - [x] PHI alteration/destruction protection
- [x] Transmission Security (§164.312(e)(1))
  - [x] Guard against unauthorized access

### Security Testing

**Required Testing**:
1. **Authentication Testing**: Verify token generation and validation
2. **Authorization Testing**: Test role-based access controls
3. **Encryption Testing**: Verify data encryption/decryption
4. **Input Validation Testing**: SQL injection, XSS prevention
5. **Session Management Testing**: Token expiration and renewal

**Test Examples**:
```python
def test_unauthorized_access():
    response = client.get("/patients")
    assert response.status_code == 401

def test_role_based_access():
    # Nurse shouldn't create patients
    response = client.post("/patients", headers=nurse_headers)
    assert response.status_code == 403
```

## Security Incident Procedures

### Data Breach Response

1. **Immediate Actions**:
   - Isolate affected systems
   - Preserve audit logs
   - Notify security team

2. **Investigation**:
   - Review audit logs
   - Identify scope of breach
   - Document findings

3. **Notification Requirements**:
   - Affected individuals: Within 60 days
   - HHS: Within 60 days
   - Media (if >500 individuals): Within 60 days

### Regular Security Reviews

**Monthly**:
- Review access logs for anomalies
- Check for failed login patterns
- Verify backup integrity

**Quarterly**:
- Security patch updates
- Permission audit
- Encryption key rotation

**Annually**:
- Full security assessment
- Penetration testing
- HIPAA compliance audit

## Conclusion

This Medical Records API implements comprehensive security measures to protect patient health information in compliance with HIPAA requirements. Regular security assessments and updates are essential to maintain the security posture of the system.