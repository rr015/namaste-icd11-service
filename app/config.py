# app/config.py
import os
from dotenv import load_dotenv
from typing import Optional
import secrets

# Load environment variables from .env file

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

class Settings:
    """Application settings management"""
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # WHO ICD-API - Use getenv with proper error handling
    WHO_ICD_CLIENT_ID: Optional[str] = os.getenv("WHO_ICD_CLIENT_ID")
    WHO_ICD_CLIENT_SECRET: Optional[str] = os.getenv("WHO_ICD_CLIENT_SECRET")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./terminology.db")
    
    def __init__(self):
        self.validate()
    
    def validate(self):
        """Validate and set default values"""
        # Generate SECRET_KEY if not set
        if not self.SECRET_KEY:
            self.SECRET_KEY = secrets.token_urlsafe(32)
            print("⚠️  Generated SECRET_KEY for development")
        
        # Check if WHO API credentials are provided
        self.who_api_configured = bool(self.WHO_ICD_CLIENT_ID and self.WHO_ICD_CLIENT_SECRET)
        
        if self.who_api_configured:
            print("✅ WHO ICD-API credentials found")
        else:
            print("ℹ️ WHO ICD-API credentials not found. Using demo data.")
        
        # Debug: Show what's loaded (will be removed in production)
        print(f"🔧 Loaded WHO_ICD_CLIENT_ID: {self.WHO_ICD_CLIENT_ID[:10]}..." if self.WHO_ICD_CLIENT_ID else "❌ WHO_ICD_CLIENT_ID: Not found")
        print(f"🔧 Loaded WHO_ICD_CLIENT_SECRET: {'*' * 10}..." if self.WHO_ICD_CLIENT_SECRET else "❌ WHO_ICD_CLIENT_SECRET: Not found")

# Create settings instance
settings = Settings()