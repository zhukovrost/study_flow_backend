"""
CRUD операции для ежедневных оценок пользователя
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timedelta
from typing import List, Optional
from app.models.user_feedback import UserDailyFeedback
from app.schemas.user_feedback import UserFeedbackCreate, UserFeedbackUpdate


def create_feedback(
    db: Session, 
    user_id: int, 
    feedback: UserFeedbackCreate,
    feedback_date: Optional[date] = None
) -> UserDailyFeedback:
    """
    Создать или обновить ежедневную оценку пользователя
    
    Если оценка за эту дату уже существует, она будет обновлена.
    """
    if feedback_date is None:
        feedback_date = date.today()
    
    # Проверяем, существует ли уже оценка за эту дату
    existing = db.query(UserDailyFeedback).filter(
        UserDailyFeedback.user_id == user_id,
        UserDailyFeedback.date == feedback_date
    ).first()
    
    if existing:
        # Обновляем существующую оценку
        existing.state = feedback.state
        existing.comment = feedback.comment
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Создаем новую оценку
        db_feedback = UserDailyFeedback(
            user_id=user_id,
            date=feedback_date,
            state=feedback.state,
            comment=feedback.comment
        )
        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)
        return db_feedback


def get_feedback_by_date(
    db: Session, 
    user_id: int, 
    feedback_date: date
) -> Optional[UserDailyFeedback]:
    """Получить оценку пользователя за конкретную дату"""
    return db.query(UserDailyFeedback).filter(
        UserDailyFeedback.user_id == user_id,
        UserDailyFeedback.date == feedback_date
    ).first()


def get_feedback_today(db: Session, user_id: int) -> Optional[UserDailyFeedback]:
    """Получить оценку пользователя за сегодня"""
    return get_feedback_by_date(db, user_id, date.today())


def get_feedback_history(
    db: Session, 
    user_id: int, 
    days_back: int = 30,
    skip: int = 0,
    limit: int = 100
) -> List[UserDailyFeedback]:
    """
    Получить историю оценок пользователя
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        days_back: Количество дней назад для выборки
        skip: Пропустить N записей
        limit: Максимальное количество записей
    
    Returns:
        Список оценок, отсортированный по дате (новые первыми)
    """
    start_date = date.today() - timedelta(days=days_back)
    
    return db.query(UserDailyFeedback).filter(
        UserDailyFeedback.user_id == user_id,
        UserDailyFeedback.date >= start_date
    ).order_by(UserDailyFeedback.date.desc()).offset(skip).limit(limit).all()


def state_to_numeric(state: str) -> float:
    """
    Преобразует состояние пользователя в числовое значение для расчетов
    
    Args:
        state: Состояние пользователя (выгорел, устал, в норме, полон сил)
    
    Returns:
        Числовое значение от 1.0 (выгорел) до 4.0 (полон сил)
    """
    state_map = {
        "выгорел": 1.0,
        "устал": 2.0,
        "в норме": 3.0,
        "полон сил": 4.0
    }
    return state_map.get(state, 2.5)  # По умолчанию среднее значение


def get_average_feedback_score(
    db: Session, 
    user_id: int, 
    days_back: int = 7
) -> Optional[float]:
    """
    Получить среднее числовое значение состояний пользователя за период
    
    Returns:
        Среднее значение (1.0-4.0) или None, если нет данных
    """
    start_date = date.today() - timedelta(days=days_back)
    
    feedbacks = db.query(UserDailyFeedback).filter(
        UserDailyFeedback.user_id == user_id,
        UserDailyFeedback.date >= start_date
    ).all()
    
    if not feedbacks:
        return None
    
    # Преобразуем состояния в числовые значения и вычисляем среднее
    numeric_values = [state_to_numeric(f.state) for f in feedbacks]
    return sum(numeric_values) / len(numeric_values) if numeric_values else None


def get_most_common_state(
    db: Session,
    user_id: int,
    days_back: int = 7
) -> Optional[str]:
    """
    Получить наиболее частое состояние пользователя за период
    
    Returns:
        Наиболее частое состояние или None, если нет данных
    """
    from collections import Counter
    
    start_date = date.today() - timedelta(days=days_back)
    
    feedbacks = db.query(UserDailyFeedback).filter(
        UserDailyFeedback.user_id == user_id,
        UserDailyFeedback.date >= start_date
    ).all()
    
    if not feedbacks:
        return None
    
    states = [f.state for f in feedbacks]
    counter = Counter(states)
    return counter.most_common(1)[0][0] if counter else None


def get_recent_feedback_for_risk_calculation(
    db: Session,
    user_id: int,
    target_date: date,
    days_back: int = 7
) -> Optional[float]:
    """
    Получить среднее числовое значение состояний пользователя за период для корректировки индекса риска
    
    Используется для корректировки индекса риска выгорания на основе
    субъективной оценки пользователя.
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        target_date: Дата, для которой рассчитывается риск
        days_back: Количество дней назад для усреднения
    
    Returns:
        Среднее числовое значение (1.0-4.0) за период или None, если нет данных
    """
    start_date = target_date - timedelta(days=days_back)
    
    feedbacks = db.query(UserDailyFeedback).filter(
        UserDailyFeedback.user_id == user_id,
        UserDailyFeedback.date >= start_date,
        UserDailyFeedback.date <= target_date
    ).all()
    
    if not feedbacks:
        return None
    
    # Преобразуем состояния в числовые значения и вычисляем среднее
    numeric_values = [state_to_numeric(f.state) for f in feedbacks]
    return sum(numeric_values) / len(numeric_values) if numeric_values else None

