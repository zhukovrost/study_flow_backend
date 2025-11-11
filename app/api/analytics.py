"""
API endpoints для аналитики продуктивности
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.base import get_db
from app.models.user import User
from app.deps import get_current_active_user
from app.crud import analytics as crud_analytics
from app.analytics import calculate_productivity_metrics, get_top_weekdays
from app.schemas.analytics import (
    ProductivityMetrics,
    AnalyticsDashboard,
    ProductivityRecommendation,
    BurnoutWarning,
    TopWeekday
)

router = APIRouter()

# Названия дней недели
WEEKDAY_NAMES = {
    0: "Понедельник",
    1: "Вторник",
    2: "Среда",
    3: "Четверг",
    4: "Пятница",
    5: "Суббота",
    6: "Воскресенье"
}


def format_recommendation(top_weekdays_data: list) -> ProductivityRecommendation:
    """Форматирование рекомендации по продуктивности"""
    if not top_weekdays_data:
        return ProductivityRecommendation(
            message="Недостаточно данных для анализа",
            top_weekdays=[],
            suggestion="Продолжайте работать, чтобы получить рекомендации"
        )
    
    top_days = [WEEKDAY_NAMES.get(w['weekday'], f"День {w['weekday']}") for w in top_weekdays_data]
    
    if len(top_days) == 1:
        suggestion = f"Планируйте сложные задачи на {top_days[0]}"
    else:
        suggestion = f"Планируйте сложные задачи на {top_days[0]} и {top_days[1]}"
    
    return ProductivityRecommendation(
        message=f"Ваши самые продуктивные дни: {', '.join(top_days)}",
        top_weekdays=top_days,
        suggestion=suggestion
    )


def format_burnout_warning(risk_category: str, risk_index: float) -> Optional[BurnoutWarning]:
    """Форматирование предупреждения о риске выгорания"""
    if risk_category == "низкий":
        return None
    
    suggestions = []
    
    if risk_category == "средний":
        message = "Обнаружен средний риск перегрузки. Рекомендуется снизить темп."
        suggestions = [
            "Разгрузите план на ближайшие дни",
            "Попробуйте разорвать стрик «лёгким днём»",
            "Уменьшите количество задач на 20-30%"
        ]
    else:  # высокий
        message = "Высокий риск перегрузки! Необходимо срочно снизить нагрузку."
        suggestions = [
            "Срочно разгрузите план на ближайшую неделю",
            "Обязательно разорвите стрик «лёгким днём»",
            "Уменьшите количество задач минимум на 40%",
            "Рассмотрите возможность короткого перерыва"
        ]
    
    return BurnoutWarning(
        category=risk_category,
        message=message,
        suggestions=suggestions
    )


@router.get("/metrics", response_model=ProductivityMetrics)
def get_productivity_metrics(
    days_back: int = 60,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получить метрики продуктивности
    """
    # Получаем данные по дням
    daily_data = crud_analytics.get_daily_tasks_data(db, user_id=current_user.id, days_back=days_back)
    
    if not daily_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Недостаточно данных для анализа. Нужно минимум несколько дней активности."
        )
    
    # Вычисляем метрики
    metrics_dict = calculate_productivity_metrics(daily_data)
    
    # Преобразуем в схему
    from app.schemas.analytics import BurnoutComponents, BurnoutRisk, MovingAverages, TopWeekday
    
    return ProductivityMetrics(
        weekday_productivity=metrics_dict['weekday_productivity'],
        top_weekdays=[
            TopWeekday(weekday=w['weekday'], mean_tasks=w['mean_tasks'])
            for w in metrics_dict['top_weekdays']
        ],
        adj_tasks=metrics_dict['adj_tasks'],
        factors=metrics_dict['factors'],
        moving_averages=MovingAverages(**metrics_dict['moving_averages']),
        ema_values=metrics_dict['ema_values'],
        z_score=metrics_dict['z_score'],
        burnout_risk=BurnoutRisk(
            index=metrics_dict['burnout_risk']['index'],
            category=metrics_dict['burnout_risk']['category'],
            components=BurnoutComponents(**metrics_dict['burnout_risk']['components'])
        ),
        dates=metrics_dict['dates'],
        tasks_raw=metrics_dict['tasks_raw'],
        streaks=metrics_dict['streaks']
    )


@router.get("/dashboard", response_model=AnalyticsDashboard)
def get_analytics_dashboard(
    days_back: int = 60,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получить полный дашборд аналитики с рекомендациями и предупреждениями
    """
    # Получаем метрики
    metrics = get_productivity_metrics(days_back=days_back, db=db, current_user=current_user)
    
    # Формируем рекомендацию
    recommendation = format_recommendation(metrics.top_weekdays)
    
    # Формируем предупреждение о риске
    warning = format_burnout_warning(metrics.burnout_risk.category, metrics.burnout_risk.index)
    
    return AnalyticsDashboard(
        metrics=metrics,
        recommendation=recommendation,
        warning=warning
    )


@router.get("/risk", response_model=BurnoutWarning)
def get_burnout_risk(
    days_back: int = 60,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получить информацию о риске выгорания
    """
    # Получаем метрики
    metrics = get_productivity_metrics(days_back=days_back, db=db, current_user=current_user)
    
    # Формируем предупреждение
    warning = format_burnout_warning(metrics.burnout_risk.category, metrics.burnout_risk.index)
    
    if not warning:
        # Если риск низкий, возвращаем позитивное сообщение
        return BurnoutWarning(
            category="низкий",
            message="Риск перегрузки низкий. Продолжайте в том же темпе!",
            suggestions=["Поддерживайте текущий баланс нагрузки"]
        )
    
    return warning


@router.get("/recommendations", response_model=ProductivityRecommendation)
def get_recommendations(
    days_back: int = 60,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получить рекомендации по продуктивности
    """
    # Получаем метрики
    metrics = get_productivity_metrics(days_back=days_back, db=db, current_user=current_user)
    
    # Формируем рекомендацию
    return format_recommendation(metrics.top_weekdays)

