"""
Конфигурация приложения
"""
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Настройки приложения из переменных окружения
    """
    # Название проекта
    PROJECT_NAME: str = "StudyFlow"
    PROJECT_VERSION: str = "1.0.0"
    
    # Настройки базы данных
    DATABASE_URL: str = "sqlite:///./studyflow.db"
    
    # Настройки JWT
    SECRET_KEY: str = "your-secret-key-please-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Дополнительные настройки
    API_V1_STR: str = "/api/v1"
    
    # Настройки YandexGPT
    YANDEXGPT_API_KEY: Optional[str] = None
    YANDEXGPT_FOLDER_ID: Optional[str] = None
    YANDEXGPT_MODEL: str = "yandexgpt-5.1"
    
    # Настройки Google AI
    GOOGLE_AI_API_KEY: Optional[str] = None
    GOOGLE_AI_MODEL: str = "gemini-2.5-flash"
    
    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = Settings()





