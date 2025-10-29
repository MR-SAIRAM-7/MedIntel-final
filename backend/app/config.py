"""
Configuration management for MedIntel application.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")


class Config:
    """Application configuration class."""
    
    # MongoDB Configuration
    MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    DB_NAME = os.environ.get("DB_NAME", "medintel_db")
    
    # AI Configuration
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
    
    # Server Configuration
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", 8001))
    RELOAD = os.environ.get("RELOAD", "true").lower() == "true"
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")
    
    # File Upload Configuration
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    ALLOWED_DOCUMENT_TYPES = ["application/pdf", "text/plain"]
    
    # AI Model Configuration
    AI_MODEL_NAMES = ["gemini-2.0-flash", "gemini-1.5-flash"]
    AI_TEMPERATURE = 0.7
    AI_MAX_OUTPUT_TOKENS = 1500
    AI_MAX_RETRIES = 3
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.MONGO_URL:
            raise RuntimeError("MONGO_URL is required")
        if not cls.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is required for AI functionality")
        return True


# Create configuration instance
config = Config()
