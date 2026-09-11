import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    # Core Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "campus_ai_agent_default_secret_key_2026")
    DATABASE_PATH = BASE_DIR / "campus_agent.db"
    UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
    RESUMES_FOLDER = BASE_DIR / "static" / "uploads" / "resumes"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
    ALLOWED_RESUME_EXTENSIONS = {"pdf", "docx", "doc", "txt"}
    ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_RESUME_EXTENSIONS
    
    # OpenRouter AI
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    
    # Google OAuth 2.0
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:5000/api/auth/google/callback")
    
    # SMS / WhatsApp Notification Gateway
    SMS_PROVIDER_API_KEY = os.getenv("SMS_PROVIDER_API_KEY", "")
    SMS_PROVIDER_SENDER_ID = os.getenv("SMS_PROVIDER_SENDER_ID", "CAMPUS_AGENT")
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")
    
    # Email SMTP
    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
    EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    
    # Automation Scheduler Intervals
    INTERNSHIP_SCAN_HOURS = int(os.getenv("INTERNSHIP_SCAN_HOURS", 6))
    SCHOLARSHIP_SCAN_HOURS = int(os.getenv("SCHOLARSHIP_SCAN_HOURS", 12))
    EVENT_SCAN_HOURS = int(os.getenv("EVENT_SCAN_HOURS", 6))
    DEADLINE_CHECK_HOURS = int(os.getenv("DEADLINE_CHECK_HOURS", 1))
    
    # Server configuration
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("FLASK_ENV", "development") == "development"
