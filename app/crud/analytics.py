"""
CRUD операции для аналитики
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from collections import defaultdict

from app.models.task import Task


def get_daily_tasks_data(
    db: Session,
    user_id: int,
    days_back: int = 60
) -> List[Dict]:
    """
    Получить данные по выполненным задачам по дням
    Возвращает список словарей с ключами: date, tasks_done, streak
    """
    # Вычисляем начальную дату
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days_back)
    
    # Получаем все выполненные задачи пользователя за период
    # Используем completed_at если есть, иначе created_at
    tasks = db.query(Task).filter(
        and_(
            Task.owner_id == user_id,
            Task.is_completed == True
        )
    ).all()
    
    # Группируем по датам завершения
    daily_counts = defaultdict(int)
    for task in tasks:
        # Используем completed_at если есть, иначе created_at
        if task.completed_at:
            task_date = task.completed_at.date() if isinstance(task.completed_at, datetime) else task.completed_at
        else:
            task_date = task.created_at.date() if isinstance(task.created_at, datetime) else task.created_at
        
        # Фильтруем по периоду
        if start_date <= task_date <= end_date:
            daily_counts[task_date] += 1
    
    # Создаем список всех дней в периоде
    result = []
    current_date = start_date
    current_streak = 0
    max_streak = 0
    
    # Проходим по всем дням и вычисляем streak
    while current_date <= end_date:
        tasks_done = daily_counts.get(current_date, 0)
        
        # Обновляем streak
        if tasks_done > 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
        
        result.append({
            'date': current_date,
            'tasks_done': tasks_done,
            'streak': current_streak
        })
        
        current_date += timedelta(days=1)
    
    # Теперь проходим еще раз, чтобы установить правильный streak для каждого дня
    # (streak должен быть текущим на момент этого дня)
    current_streak = 0
    for i, record in enumerate(result):
        if record['tasks_done'] > 0:
            current_streak += 1
        else:
            current_streak = 0
        record['streak'] = current_streak
    
    return result


def get_completed_tasks_by_date_range(
    db: Session,
    user_id: int,
    start_date: date,
    end_date: date
) -> List[Task]:
    """
    Получить выполненные задачи за период
    """
    return db.query(Task).filter(
        and_(
            Task.owner_id == user_id,
            Task.is_completed == True,
            func.date(Task.created_at) >= start_date,
            func.date(Task.created_at) <= end_date
        )
    ).order_by(Task.created_at).all()

