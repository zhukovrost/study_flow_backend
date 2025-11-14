"""
Pydantic схемы для пользователя
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Базовая схема пользователя"""
    email: EmailStr
    username: str
    name: Optional[str] = None
    surname: Optional[str] = None


class UserCreate(UserBase):
    """Схема для создания пользователя"""
    password: str


class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    name: Optional[str] = None
    surname: Optional[str] = None


class UserInDB(UserBase):
    """Схема пользователя в БД"""
    id: int
    
    class Config:
        from_attributes = True


class User(UserInDB):
    """Публичная схема пользователя"""
    pass


class UserLogin(BaseModel):
    """Схема для входа"""
    username: str
    password: str


class Token(BaseModel):
    """Схема токена"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Данные из токена"""
    username: Optional[str] = None
