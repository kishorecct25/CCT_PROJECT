"""
Configuration settings for the CCT Backend application.
"""
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "CCT Backend"
    API_VERSION: str = "v1"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres.wyaakivfwtnygtyhjxka:uubrgd9sikPwwV9t@aws-0-us-east-2.pooler.supabase.com:6543/postgres")
    
    # JWT Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "rWN2mG8GqRQV762w")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Notification settings
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "False").lower() == "true"
    SMS_ENABLED: bool = os.getenv("SMS_ENABLED", "False").lower() == "true"
    PUSH_ENABLED: bool = os.getenv("PUSH_ENABLED", "True").lower() == "true"
    
    # Email configuration
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.example.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@cctapp.com")
    
    # SMS configuration
    SMS_PROVIDER_API_KEY: str = os.getenv("SMS_PROVIDER_API_KEY", "")
    SMS_PROVIDER_URL: str = os.getenv("SMS_PROVIDER_URL", "")
    
    # Push notification configuration
    FIREBASE_CREDENTIALS: str = os.getenv("FIREBASE_CREDENTIALS", "")
    
    # Device settings
    MAX_PROBES_PER_CCT: int = 4
    TEMPERATURE_UPDATE_INTERVAL_SECONDS: int = 10
    
    # Connection monitoring
    CONNECTION_TIMEOUT_SECONDS: int = 60
    
    class Config:
        env_file = ".env"

settings = Settings()
