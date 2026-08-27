import os
from typing import List
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ChargeShield"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    SECRET_KEY: str = "chargeshield-dev-secret-key-change-in-production"
    
    # JWT Authentication Security
    JWT_SECRET_KEY: str = "chargeshield-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    
    # Rate Limiting & Upload Hardening
    RATE_LIMIT_PER_MINUTE: int = 60
    MAX_UPLOAD_SIZE_BYTES: int = 10485760  # 10 MB
    
    DATABASE_URL: str = "sqlite:///./chargeshield.db"
    
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:8000"
    ]
    
    ANTHROPIC_API_KEY: str = ""
    VITE_API_BASE_URL: str = "http://127.0.0.1:8000"
    
    # Development Seed Credentials (never default in production)
    SEED_DEV_USER: bool = False
    DEV_ADMIN_USERNAME: str = ""
    DEV_ADMIN_PASSWORD: str = ""
    
    # Disclaimer flag for synthetic data safety compliance
    DATA_IS_SYNTHETIC: bool = True
    SIMULATION_MODE: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="after")
    def validate_production_security(self):
        if self.ENVIRONMENT == "production":
            if "change-in-production" in self.JWT_SECRET_KEY.lower() or not self.JWT_SECRET_KEY:
                raise ValueError("CRITICAL SECURITY ERROR: Production deployment requires a secure JWT_SECRET_KEY environment variable.")
            if "change-in-production" in self.SECRET_KEY.lower() or not self.SECRET_KEY:
                raise ValueError("CRITICAL SECURITY ERROR: Production deployment requires a secure SECRET_KEY environment variable.")
        return self

settings = Settings()
