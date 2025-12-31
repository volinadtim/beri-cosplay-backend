from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import secrets

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Security
    BCRYPT_ROUNDS: int = 12
    
    # Admin
    ADMIN_EMAIL: str = "admin@bericosplay.com"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "Admin123!"  # Change in production
    ADMIN_FULL_NAME: str = "Admin User"
    
    # App
    PROJECT_NAME: str = "Beri Cosplay API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Debug
    DEBUG: bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

settings = Settings()