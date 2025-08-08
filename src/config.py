"""
Application configuration settings.
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Server Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    FRONTEND_PORT: int = 7860
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # External API Keys
    OPENROUTER_API_KEY: Optional[str] = None
    STABLE_DIFFUSION_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    HUGGINGFACE_API_KEY: Optional[str] = None
    
    # Default Model Settings
    DEFAULT_CHAT_MODEL: str = "gpt-4"
    DEFAULT_IMAGE_MODEL: str = "stabilityai/stable-diffusion-2-1"
    DEFAULT_SD_STEPS: int = 30
    DEFAULT_SD_CFG_SCALE: float = 7.5
    DEFAULT_SD_WIDTH: int = 512
    DEFAULT_SD_HEIGHT: int = 512
    
    # API Routes
    API_PREFIX: str = "/api/v1"
    
    # CORS Configuration
    ALLOWED_ORIGINS: str = "*"
    ALLOWED_METHODS: str = "*"
    ALLOWED_HEADERS: str = "*"
    
    @property
    def CHAT_ENDPOINT(self) -> str:
        return f"{self.API_PREFIX}/chat"
    
    @property
    def PERSONA_ENDPOINT(self) -> str:
        return f"{self.API_PREFIX}/persona"
    
    @property
    def IMAGE_ENDPOINT(self) -> str:
        return f"{self.API_PREFIX}/image"
        
    @property
    def cors_config(self) -> dict:
        """Get CORS configuration."""
        return {
            "allow_origins": self.ALLOWED_ORIGINS.split(",") if "," in self.ALLOWED_ORIGINS else [self.ALLOWED_ORIGINS],
            "allow_methods": self.ALLOWED_METHODS.split(",") if "," in self.ALLOWED_METHODS else [self.ALLOWED_METHODS],
            "allow_headers": self.ALLOWED_HEADERS.split(",") if "," in self.ALLOWED_HEADERS else [self.ALLOWED_HEADERS],
            "allow_credentials": True,
        }
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True
        extra = 'ignore'  # Ignore extra environment variables

# Create settings instance
settings = Settings()
