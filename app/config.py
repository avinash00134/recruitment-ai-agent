from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from logger import logger
import os
from pathlib import Path

class settings(BaseSettings):
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    APP_NAME: str = "Recruitment AI Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    MAX_RESUMES: int = 10
    MODEL_NAME: str = "gpt-3.5-turbo"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        env_file_encoding = 'utf-8'  # Explicitly set encoding

# Alternative approach if the above doesn't work
def load_settings_safely():
    """Load settings with fallback for encoding issues"""
    try:
        return settings()
    except UnicodeDecodeError as e:
        logger.warning(f"Encoding issue with .env file: {e}. Trying alternative approach...")
        
        # Try to read the .env file manually and set environment variables
        env_path = Path(".env")
        if env_path.exists():
            try:
                # Try different encodings
                for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                    try:
                        with open(env_path, 'r', encoding=encoding) as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#') and '=' in line:
                                    key, value = line.split('=', 1)
                                    os.environ[key.strip()] = value.strip()
                        break
                    except UnicodeDecodeError:
                        continue
                
                # Now try to create settings again
                return settings()
            except Exception as inner_e:
                logger.error(f"Failed to read .env file: {inner_e}")
        
        # If all else fails, try to get from environment directly
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        return settings(
            OPENAI_API_KEY=api_key,
            APP_NAME=os.environ.get("APP_NAME", "Recruitment AI Agent"),
            APP_VERSION=os.environ.get("APP_VERSION", "1.0.0"),
            DEBUG=os.environ.get("DEBUG", "False").lower() == "true",
            MAX_RESUMES=int(os.environ.get("MAX_RESUMES", "10")),
            MODEL_NAME=os.environ.get("MODEL_NAME", "gpt-3.5-turbo")
        )

try:
    settings = load_settings_safely()
    logger.info("Configuration loaded successfully")
except Exception as e:
    logger.error(f"Error loading configuration: {str(e)}")
    raise