# Enhanced Medical Consultation System

An AI-powered medical consultation assistant that combines RAG (Retrieval-Augmented Generation) with agentic workflows to provide comprehensive medical information and guidance.

## 🏥 Overview

This system implements a sophisticated medical consultation platform that:
- Conducts intelligent patient interviews
- Performs symptom analysis and verification
- Generates differential diagnoses
- Provides actionable recommendations
- Integrates with medical knowledge bases
- Ensures safety through multiple validation layers

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager
- At least 4GB of RAM
- Internet connection for API access

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd TestB
```

2. **Create virtual environment (recommended)**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
Create a `.env` file in the project root:
```env
# Required: Groq API Key (already configured in config.py)
GROQ_API_KEY=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

# Optional: OpenAI API Key (if you want to use OpenAI instead)
# OPENAI_API_KEY=your_openai_api_key_here

# Optional: Custom API endpoints
# ULTRASAFE_API_KEY=your_api_key_here
```

5. **Run the application**
```bash
python -m streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## 📁 Project Structure

```
TestB/
├── app.py                  # Main Streamlit application
├── orchestrator.py         # LangGraph workflow orchestration
├── agents.py              # AI agents for different tasks
├── models.py              # Pydantic data models
├── knowledge_base.py      # RAG implementation with ChromaDB
├── ultrasafe_client.py    # External API client
├── config.py              # Configuration and settings
├── evaluation.py          # System evaluation framework
├── requirements.txt       # Python dependencies
└── medical_db/           # ChromaDB persistence (auto-created)
```

## 🎯 Key Features

### 1. **Intelligent Patient Interview**
- Adaptive questioning based on responses
- Symptom extraction with NLP
- Context-aware follow-up questions

### 2. **RAG-Powered Knowledge Base**
- Vector similarity search using ChromaDB
- Hybrid retrieval with metadata filtering
- Medical condition database with symptoms and treatments

### 3. **Agentic Workflow**
- State-based conversation management
- Multi-agent collaboration
- Automatic workflow progression

### 4. **Safety Features**
- Emergency detection and alerts
- Drug interaction checking
- Professional referral recommendations
- Clear medical disclaimers

### 5. **Comprehensive Reporting**
- Detailed consultation summaries
- Exportable JSON reports
- Session tracking and history

## 🧪 Testing

Run the evaluation suite:
```bash
python evaluation.py
```

This will:
- Test diagnostic accuracy
- Evaluate safety compliance
- Measure API performance
- Assess user experience
- Generate a detailed report

## 📊 System Architecture

The system uses a modular architecture with:
- **LangGraph** for workflow orchestration
- **LangChain** for LLM integration
- **ChromaDB** for vector storage
- **Groq API** for fast LLM inference
- **Streamlit** for the web interface

## 🔧 Configuration

### Switching LLM Providers

To use OpenAI instead of Groq, modify `config.py`:
```python
# Comment out Groq settings
# GROQ_API_KEY = "..."
# LLM_MODEL = "llama-3.3-70b-versatile"

# Uncomment OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = "gpt-4-turbo-preview"
```

### Adjusting System Parameters

Edit `config.py` to modify:
- `MAX_CONSULTATION_LENGTH`: Maximum conversation turns
- `CONFIDENCE_THRESHOLD`: Minimum confidence for diagnoses
- `EMERGENCY_RESPONSE_TIME`: Timeout for critical cases

## 🛠️ Troubleshooting

### Common Issues

1. **Import errors**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **API errors**: The UltraSafe API is a mock service. These errors are expected and handled gracefully.

3. **Memory issues**: If using large models, ensure sufficient RAM or switch to smaller models.

4. **ChromaDB errors**: Delete the `medical_db` folder and restart to reset the database.

## 📝 License

This project is for educational and demonstration purposes.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!