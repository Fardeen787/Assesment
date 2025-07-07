# Implementation Details

## 🏗️ System Architecture

### Core Components

#### 1. **Orchestrator (`orchestrator.py`)**
The central coordinator that manages the entire consultation workflow using LangGraph.

**Key Implementation Details:**
- **StateGraph**: Implements a directed graph workflow with `ConsultationState` as the shared state
- **Nodes**: Each step in the consultation process (interview, verification, diagnosis, etc.)
- **Edges**: Define transitions between steps with conditional routing
- **Async Execution**: All methods are async for non-blocking API calls

```python
# Workflow progression
start → interview → verify_symptoms → retrieve_knowledge → 
check_interactions → diagnose → recommend → find_providers → end
```

#### 2. **AI Agents (`agents.py`)**

**EnhancedPatientInterviewAgent**
- Uses LLM to generate contextual questions
- Implements sophisticated symptom extraction with JSON parsing
- Fallback mechanisms for common symptom patterns
- Maintains conversation history to avoid repetition

**EnhancedMedicalKnowledgeAgent**
- Interfaces with the ChromaDB knowledge base
- Performs hybrid search (vector + metadata)
- Retrieves relevant medical conditions

**EnhancedDifferentialDiagnosisAgent**
- Analyzes symptoms against retrieved conditions
- Calculates confidence scores using:
  - Symptom matching
  - Severity alignment
  - Patient demographics
  - Risk factors

**EnhancedRecommendationAgent**
- Generates actionable recommendations
- Prioritizes by urgency
- Includes safety warnings
- Suggests appropriate healthcare providers

#### 3. **RAG Implementation (`knowledge_base.py`)**

**Vector Database Setup:**
- **ChromaDB** for persistent vector storage
- **SentenceTransformer** (all-MiniLM-L6-v2) for embeddings
- **Metadata Filtering** for targeted retrieval

**Key Features:**
- Hybrid search combining vector similarity and metadata filters
- Automatic embedding generation for medical conditions
- Severity-based filtering
- Efficient retrieval with configurable result limits

**Search Strategy:**
```python
1. Generate query embedding
2. Search with metadata filters (severity, symptoms)
3. Rank by relevance score
4. Return top K results
```

#### 4. **Data Models (`models.py`)**

Comprehensive Pydantic models ensure data validation:

- **Severity Enum**: Standardized severity levels (LOW, MODERATE, HIGH, CRITICAL)
- **Symptom**: Detailed symptom representation with location, duration, triggers
- **PatientInfo**: Demographics, medical history, medications
- **MedicalCondition**: ICD codes, symptoms, treatments, risk factors
- **ConsultationState**: Complete session state management

#### 5. **External API Integration (`ultrasafe_client.py`)**

Mock implementation demonstrating:
- Async HTTP requests with aiohttp
- Retry logic with exponential backoff
- Error handling and logging
- Response parsing and validation

### 🔄 Workflow Implementation

#### State Management
```python
ConsultationState:
  - session_id: Unique identifier
  - patient_info: Demographics and history
  - symptoms: List of identified symptoms
  - conversation_history: Full chat log
  - diagnoses: Differential diagnosis list
  - recommendations: Action items
  - current_step: Workflow position
  - metadata: Additional tracking data
```

#### Conversation Flow
1. **Initialization**: Welcome message with disclaimers
2. **Interview Loop**: 
   - Generate question based on current state
   - Extract symptoms from response
   - Update state
   - Check if more information needed
3. **Processing Pipeline**:
   - Verify symptoms with external API
   - Retrieve relevant conditions from knowledge base
   - Check drug interactions
   - Generate diagnoses with confidence scores
   - Create recommendations
   - Find healthcare providers
4. **Completion**: Generate summary and export options

### 🎨 UI Implementation (`app.py`)

**Streamlit Components:**
- Session state management for persistence
- Custom CSS for professional appearance
- Real-time updates with `st.rerun()`
- Progress indicators for long operations
- Collapsible sections for better UX

**Key Features:**
- Responsive design with mobile support
- Color-coded severity indicators
- Export functionality (JSON reports)
- Clear visual hierarchy
- Accessibility considerations

### 🧪 Evaluation Framework (`evaluation.py`)

**Comprehensive Testing:**
- Predefined test cases covering common scenarios
- Metrics calculation for accuracy, safety, performance
- Edge case handling tests
- Automated report generation

**Metrics Tracked:**
- Diagnostic accuracy (precision/recall)
- Urgency classification accuracy
- API performance (response time, success rate)
- Safety compliance (emergency detection, disclaimers)
- User experience (question quality, completeness)

### 🔐 Safety Implementation

**Multiple Safety Layers:**
1. **Input Validation**: All user inputs validated through Pydantic
2. **Emergency Detection**: Critical symptoms trigger immediate alerts
3. **Drug Interaction Checking**: Cross-references medications
4. **Professional Referrals**: Always recommends consulting healthcare providers
5. **Clear Disclaimers**: Prominent medical disclaimers throughout

### 📊 Performance Optimizations

1. **Async Operations**: Non-blocking API calls
2. **Caching**: ChromaDB persistence reduces redundant computations
3. **Batch Processing**: Multiple symptoms processed together
4. **Efficient Embeddings**: Lightweight sentence transformer model
5. **Connection Pooling**: Reusable HTTP sessions

### 🔧 Error Handling

**Graceful Degradation:**
- API failures don't crash the system
- Fallback data for demonstration
- Comprehensive logging for debugging
- User-friendly error messages
- Automatic retry mechanisms

### 📝 Logging and Monitoring

- Structured logging throughout the application
- API call tracking for usage analytics
- Performance metrics collection
- Error tracking with stack traces
- Session-based log segregation