# Implementation Details - Medical Records API

## Architecture Overview

The Medical Records API is built using a layered architecture pattern with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│           API Layer (FastAPI)           │
├─────────────────────────────────────────┤
│        Business Logic Layer             │
│  (Security, Audit, Vector Search)       │
├─────────────────────────────────────────┤
│         Data Access Layer               │
│    (SQLAlchemy ORM + Models)           │
├─────────────────────────────────────────┤
│         Database Layer                  │
│    (SQLite/PostgreSQL Ready)           │
└─────────────────────────────────────────┘
```

## Core Components

### 1. API Layer (main.py)

**FastAPI Application**
- Implements RESTful endpoints for all operations
- Handles request/response validation using Pydantic
- Manages authentication flow with OAuth2
- Implements middleware for request logging

**Key Features:**
- Automatic API documentation generation
- Request validation with detailed error messages
- Async request handling for better performance
- CORS middleware for frontend integration

### 2. Data Models (models.py)

**SQLAlchemy Models:**

```python
User
├── id (Primary Key)
├── username (Unique)
├── email (Unique)
├── hashed_password
├── role (admin/doctor/nurse)
└── relationships → permissions, audit_logs

Patient
├── id (Primary Key)
├── personal information
├── ssn_encrypted
└── relationships → medical_records

MedicalRecord
├── id (Primary Key)
├── patient_id (Foreign Key)
├── encrypted fields (diagnosis, treatment, notes)
└── relationships → patient, creator

AccessPermission
├── user_id (Foreign Key)
├── resource
└── action

AuditLog
├── user_id (Foreign Key)
├── action details
└── timestamp
```

### 3. Security Implementation (security.py)

**SecurityManager Class:**

1. **Encryption/Decryption**
   - Uses Fernet symmetric encryption
   - Base64 encoding for storage
   - Automatic key generation if not provided

2. **Data Anonymization**
   - Patient identifier masking
   - SSN partial redaction
   - Email masking
   - Complete address redaction

3. **Access Control Matrix**
   ```python
   {
     "admin": {"*": ["*"]},
     "doctor": {
       "patients": ["read", "write"],
       "medical_records": ["read", "write"]
     },
     "nurse": {
       "patients": ["read"],
       "medical_records": ["read"]
     }
   }
   ```

### 4. Vector Store Implementation (vector_store.py)

**Current Implementation:**
- In-memory document storage
- Simple keyword-based matching
- Metadata filtering support
- Score normalization

**Vector Search Process:**
1. Document addition with metadata
2. Simple embedding generation (placeholder)
3. Query processing with term matching
4. Result ranking by relevance score
5. Optional reranking for clinical relevance

### 5. Audit Logging (audit.py)

**AuditLogger Class:**
- Tracks all user actions
- Records API request details
- Stores additional context data
- Enables compliance reporting

**Logged Information:**
- User ID and action type
- Resource type and ID
- Timestamp
- IP address (when available)
- Additional metadata as JSON

## Authentication & Authorization Flow

### Registration Process:
1. User submits registration data
2. Password hashed with bcrypt
3. User record created
4. Default permissions assigned based on role
5. Audit log entry created

### Login Process:
1. User submits credentials
2. Password verified against hash
3. JWT token generated with 30-minute expiry
4. Token returned to client
5. Login action logged

### Request Authorization:
1. JWT token extracted from Authorization header
2. Token decoded and validated
3. User loaded from database
4. Permission checked against resource/action
5. Request processed or rejected

## Data Encryption Strategy

### Encrypted Fields:
- Patient SSN
- Medical diagnosis
- Treatment details
- Clinical notes

### Encryption Process:
1. Plain text encoded to UTF-8 bytes
2. Fernet cipher encrypts data
3. Result base64 encoded
4. Stored in database as string

### Decryption Process:
1. Base64 decode from storage
2. Fernet cipher decrypts
3. UTF-8 decode to string
4. Returned to authorized user

## Search Implementation

### Current Approach:
1. **Document Indexing**
   - Medical records added to vector store
   - Metadata preserved for filtering
   - Simple text representation stored

2. **Search Process**
   - Query terms extracted and normalized
   - Documents scored by term matches
   - Results filtered by metadata
   - Scores normalized by query length

3. **Result Processing**
   - Top-k results selected
   - Optional anonymization applied
   - Clinical reranking (placeholder)
   - Audit trail created

## Database Design

### Schema Considerations:
- **Normalization**: 3NF for data integrity
- **Indexes**: On foreign keys and search fields
- **Constraints**: Unique constraints on usernames/emails
- **Relationships**: Properly defined with cascade options

### Migration Support:
- Alembic configuration included
- Version control for schema changes
- Rollback capability

## Testing Strategy

### Unit Tests (test_main.py):
- API endpoint testing
- Authentication flow validation
- Permission checking
- Data encryption/decryption
- Security feature verification

### Integration Tests (test_workflow.py):
- Complete user workflows
- End-to-end scenarios
- Performance validation
- Error handling verification

### Test Data Management:
- Separate test database
- Fixture-based test data
- Cleanup after tests
- Isolated test environments

## Performance Considerations

### Optimizations:
1. **Database Queries**
   - Eager loading for relationships
   - Query pagination
   - Index optimization

2. **Caching Strategy**
   - JWT token caching
   - Permission caching
   - Search result caching (future)

3. **Async Operations**
   - Non-blocking I/O
   - Concurrent request handling
   - Background task support

## Error Handling

### Standard Error Responses:
```json
{
  "detail": "Error message",
  "status_code": 400,
  "type": "validation_error"
}
```

### Error Categories:
- **400**: Bad Request (validation errors)
- **401**: Unauthorized (authentication required)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found (resource missing)
- **500**: Internal Server Error (logged for debugging)

## Monitoring & Logging

### Log Levels:
- **DEBUG**: Detailed debugging information
- **INFO**: General operational messages
- **WARNING**: Warning messages
- **ERROR**: Error messages with stack traces

### Metrics Tracked:
- API request count and latency
- Authentication success/failure rates
- Search query performance
- Database query timing