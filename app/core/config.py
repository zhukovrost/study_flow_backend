"""
Конфигурация приложения
"""
from pydantic_settings import BaseSettings
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
    
    class Config:
        env_file = ".env"


settings = Settings()





