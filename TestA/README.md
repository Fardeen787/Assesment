# Medical Records API - HIPAA-Compliant Semantic Search System

A FastAPI-based medical records management system with HIPAA-compliant security features and semantic search capabilities using RAG (Retrieval-Augmented Generation) technology.

## Features

- **HIPAA-Compliant Security**: Field-level encryption, audit logging, and role-based access control
- **Semantic Search**: Vector-based search for medical records with clinical relevance ranking
- **Multi-Role Support**: Admin, Doctor, and Nurse roles with appropriate permissions
- **RESTful API**: Comprehensive API for patient and medical record management
- **Data Anonymization**: Built-in anonymization for research and reporting
- **Audit Trail**: Complete audit logging for all system actions

## Technology Stack

- **Backend**: FastAPI (Python 3.8+)
- **Database**: SQLAlchemy with SQLite (PostgreSQL ready)
- **Authentication**: JWT tokens with OAuth2
- **Encryption**: Fernet symmetric encryption
- **Vector Store**: In-memory implementation (ChromaDB ready)
- **Testing**: Pytest with comprehensive test coverage

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd TestA
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=your-secret-key-here
   ENCRYPTION_KEY=your-encryption-key-here
   DATABASE_URL=sqlite:///./medical_records.db
   ```
   
   To generate keys:
   ```python
   from cryptography.fernet import Fernet
   import secrets
   
   # Generate encryption key
   print(f"ENCRYPTION_KEY={Fernet.generate_key().decode()}")
   
   # Generate secret key
   print(f"SECRET_KEY={secrets.token_urlsafe(32)}")
   ```

5. **Initialize the database**
   ```bash
   python create_tables.py
   ```

6. **Run the application**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## Quick Start

1. **Access the API documentation**
   - Interactive docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

2. **Register a new user**
   ```bash
   curl -X POST "http://localhost:8000/register" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "dr_smith",
       "email": "dr.smith@hospital.com",
       "password": "SecurePass123!",
       "role": "doctor"
     }'
   ```

3. **Login to get access token**
   ```bash
   curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=dr_smith&password=SecurePass123!"
   ```

4. **Use the token for authenticated requests**
   ```bash
   curl -X GET "http://localhost:8000/patients" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

## Running Tests

### Unit Tests
```bash
pytest test_main.py -v
```

### Integration Tests
```bash
# Start the server first
uvicorn main:app --reload

# In another terminal
python test_workflow.py
```

### Test Coverage
```bash
pytest --cov=. --cov-report=html
```

## API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /token` - Login and get access token

### Patients
- `POST /patients` - Create new patient
- `GET /patients` - List all patients
- `GET /patients/{patient_id}` - Get specific patient

### Medical Records
- `POST /medical-records` - Create new medical record
- `GET /medical-records/patient/{patient_id}` - Get patient's medical records

### Search
- `POST /search` - Semantic search for medical records

### Admin
- `GET /audit-logs` - View audit logs (admin only)

### Health
- `GET /` - API status
- `GET /health` - System health check

## Security Features

1. **Encryption**
   - Field-level encryption for sensitive data (SSN, diagnosis, treatment)
   - Fernet symmetric encryption with secure key management

2. **Authentication & Authorization**
   - JWT token-based authentication
   - Role-based access control (RBAC)
   - Session timeout after 30 minutes

3. **Audit Logging**
   - All API requests logged
   - User actions tracked with timestamps
   - IP address and user agent recording

4. **Data Protection**
   - Secure password hashing with bcrypt
   - HTTPS enforcement in production
   - Input validation and sanitization

## Development

### Project Structure
```
TestA/
├── main.py              # FastAPI application
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── database.py          # Database configuration
├── security.py          # Security manager
├── vector_store.py      # Vector search implementation
├── audit.py             # Audit logging
├── requirements.txt     # Dependencies
├── test_main.py         # Unit tests
├── test_workflow.py     # Integration tests
└── README.md           # This file
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints for all functions
- Document all API endpoints
- Write tests for new features

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Ensure DATABASE_URL is correctly set in .env
   - Check file permissions for SQLite database

2. **Import errors**
   - Activate virtual environment
   - Reinstall dependencies: `pip install -r requirements.txt`

3. **Authentication failures**
   - Check SECRET_KEY is set
   - Ensure token hasn't expired
   - Verify user credentials

### Debug Mode
Set logging level to DEBUG in main.py:
```python
logging.basicConfig(level=logging.DEBUG)
```

## License

This project is developed as part of a technical assessment. All rights reserved.

## Support

For issues or questions, please contact the development team or create an issue in the repository.