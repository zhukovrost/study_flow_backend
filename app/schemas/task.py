"""
Pydantic схемы для задачи
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TaskBase(BaseModel):
    """Базовая схема задачи"""
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    scheduled_date: Optional[datetime] = None
    priority: int = 1
    category_id: Optional[int] = None


class TaskCreate(TaskBase):
    """Схема для создания задачи"""
    pass


class TaskUpdate(BaseModel):
    """Схема для обновления задачи"""
    title: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None
    due_date: Optional[datetime] = None
    scheduled_date: Optional[datetime] = None
    priority: Optional[int] = None
    category_id: Optional[int] = None


class TaskInDB(TaskBase):
    """Схема задачи в БД"""
    id: int
    is_completed: bool
    created_at: datetime
    owner_id: int
    
    class Config:
        from_attributes = True


class Task(TaskInDB):
    """Публичная схема задачи"""
    pass





