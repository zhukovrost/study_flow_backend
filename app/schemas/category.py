"""
Pydantic схемы для категории
"""
from pydantic import BaseModel
from typing import Optional


class CategoryBase(BaseModel):
    """Базовая схема категории"""
    name: str


class CategoryCreate(CategoryBase):
    """Схема для создания категории"""
    pass


class CategoryUpdate(BaseModel):
    """Схема для обновления категории"""
    name: Optional[str] = None


class CategoryInDB(CategoryBase):
    """Схема категории в БД"""
    id: int
    
    class Config:
        from_attributes = True


class Category(CategoryInDB):
    """Публичная схема категории"""
    pass

