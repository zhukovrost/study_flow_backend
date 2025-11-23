"""
API endpoints для ежедневных оценок пользователя
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.base import get_db
from app.models.user import User
from app.deps import get_current_active_user
from app.schemas.user_feedback import (
    UserFeedback,
    UserFeedbackCreate,
    UserFeedbackUpdate,
    UserFeedbackHistory
)
from app.crud import user_feedback as crud_feedback

router = APIRouter()


@router.post("/", response_model=UserFeedback, status_code=status.HTTP_201_CREATED)
def create_feedback(
    feedback: UserFeedbackCreate,
    feedback_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Создать или обновить ежедневную оценку состояния
    
    Состояния: "выгорел", "устал", "в норме", "полон сил"
    
    Если оценка за указанную дату (или сегодня, если дата не указана) уже существует,
    она будет обновлена.
    """
    db_feedback = crud_feedback.create_feedback(
        db=db,
        user_id=current_user.id,
        feedback=feedback,
        feedback_date=feedback_date
    )
    return db_feedback


@router.get("/today", response_model=Optional[UserFeedback])
def get_feedback_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получить оценку состояния за сегодня
    """
    feedback = crud_feedback.get_feedback_today(db, user_id=current_user.id)
    return feedback


@router.get("/history", response_model=UserFeedbackHistory)
def get_feedback_history(
    days_back: int = 30,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получить историю оценок пользователя
    
    Returns:
        История оценок с общей статистикой
    """
    feedbacks = crud_feedback.get_feedback_history(
        db=db,
        user_id=current_user.id,
        days_back=days_back,
        skip=skip,
        limit=limit
    )
    
    # Вычисляем наиболее частое состояние
    most_common_state = crud_feedback.get_most_common_state(
        db=db,
        user_id=current_user.id,
        days_back=days_back
    )
    
    return UserFeedbackHistory(
        feedbacks=feedbacks,
        total_count=len(feedbacks),
        most_common_state=most_common_state
    )


@router.get("/{feedback_date}", response_model=Optional[UserFeedback])
def get_feedback_by_date(
    feedback_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получить оценку состояния за конкретную дату
    """
    feedback = crud_feedback.get_feedback_by_date(
        db=db,
        user_id=current_user.id,
        feedback_date=feedback_date
    )
    return feedback


@router.put("/{feedback_date}", response_model=UserFeedback)
def update_feedback(
    feedback_date: date,
    feedback: UserFeedbackUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Обновить оценку состояния за конкретную дату
    """
    existing = crud_feedback.get_feedback_by_date(
        db=db,
        user_id=current_user.id,
        feedback_date=feedback_date
    )
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Оценка за указанную дату не найдена. Используйте POST для создания."
        )
    
    # Обновляем поля
    if feedback.state is not None:
        existing.state = feedback.state
    if feedback.comment is not None:
        existing.comment = feedback.comment
    
    db.commit()
    db.refresh(existing)
    return existing

