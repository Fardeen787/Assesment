# config.py
import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = "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"
GROQ_BASE_URL = "https://api.groq.com"
EMBEDDING_MODEL = "text-embedding-ada-002"
# LLM_MODEL = "gpt-4-turbo-preview"  # OpenAI model
LLM_MODEL = "llama-3.3-70b-versatile"  # Groq model

# UltraSafe API Configuration
ULTRASAFE_BASE_URL = "https://api.ultrasafeapi.com/v1"
ULTRASAFE_API_KEY = os.getenv("ULTRASAFE_API_KEY", "demo_api_key")

# Medical Safety Configuration
MAX_CONSULTATION_LENGTH = 20
CONFIDENCE_THRESHOLD = 0.7
EMERGENCY_RESPONSE_TIME = 5  # seconds

# Create session with retry logic
def create_api_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        read=3,
        connect=3,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 504)
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session