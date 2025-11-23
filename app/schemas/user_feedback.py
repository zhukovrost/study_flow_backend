"""
Pydantic схемы для ежедневных оценок пользователя
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date, datetime
from enum import Enum


class UserState(str, Enum):
    """Состояния пользователя"""
    BURNOUT = "выгорел"
    TIRED = "устал"
    NORMAL = "в норме"
    ENERGETIC = "полон сил"


class UserFeedbackCreate(BaseModel):
    """Схема для создания ежедневной оценки"""
    state: Literal["выгорел", "устал", "в норме", "полон сил"] = Field(
        ...,
        description="Состояние пользователя: выгорел, устал, в норме, полон сил"
    )
    comment: Optional[str] = Field(None, description="Опциональный комментарий")


class UserFeedbackUpdate(BaseModel):
    """Схема для обновления оценки"""
    state: Optional[Literal["выгорел", "устал", "в норме", "полон сил"]] = None
    comment: Optional[str] = None


class UserFeedback(BaseModel):
    """Схема ежедневной оценки пользователя"""
    id: int
    user_id: int
    date: date
    state: str  # Состояние: выгорел, устал, в норме, полон сил
    comment: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserFeedbackHistory(BaseModel):
    """Схема для истории оценок"""
    feedbacks: list[UserFeedback]
    total_count: int
    most_common_state: Optional[str] = None  # Наиболее частое состояние

