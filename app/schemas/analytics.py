"""
Pydantic схемы для аналитики продуктивности
"""
from pydantic import BaseModel
from typing import List, Dict, Optional


class WeekdayProductivity(BaseModel):
    """Продуктивность по дням недели"""
    weekday: int  # 0=Monday, 6=Sunday
    mean_tasks: float
    weekday_name: Optional[str] = None


class TopWeekday(BaseModel):
    """ТОП день недели"""
    weekday: int
    mean_tasks: float


class BurnoutComponents(BaseModel):
    """Компоненты индекса риска выгорания"""
    downshift: float
    momentum: float
    zeros_rate: float
    streak_strain: float
    feedback_correction: float = 0.0  # Коррекция на основе feedback пользователя


class BurnoutRisk(BaseModel):
    """Индекс риска выгорания"""
    index: float  # 0.0 - 1.0
    category: str  # "низкий", "средний", "высокий"
    components: BurnoutComponents


class MovingAverages(BaseModel):
    """Скользящие средние"""
    mean_7: float
    mean_14: float
    mean_28: float
    std_28: float


class ProductivityMetrics(BaseModel):
    """Полные метрики продуктивности"""
    weekday_productivity: Dict[str, float]  # {weekday: mean_tasks}
    top_weekdays: List[TopWeekday]
    adj_tasks: List[float]  # Сезонно-нормализованные задачи
    factors: Dict[str, float]  # Факторы нормализации
    moving_averages: MovingAverages
    ema_values: List[float]
    z_score: float
    burnout_risk: BurnoutRisk
    dates: List[str]
    tasks_raw: List[int]
    streaks: List[int]


class ProductivityRecommendation(BaseModel):
    """Рекомендация по продуктивности"""
    message: str
    top_weekdays: List[str]  # Названия дней недели
    suggestion: str


class BurnoutWarning(BaseModel):
    """Предупреждение о риске выгорания"""
    category: str
    message: str
    suggestions: List[str]


class SupportMessage(BaseModel):
    """Сообщение поддержки для успешных пользователей"""
    type: str  # "motivation", "balance_tip", "optimization", "warning"
    text: str


class SupportRecommendations(BaseModel):
    """Рекомендации поддержки для успешных пользователей"""
    is_performing_well: bool
    messages: List[SupportMessage]
    metrics_summary: Optional[Dict] = None


class AnalyticsDashboard(BaseModel):
    """Полный дашборд аналитики"""
    metrics: ProductivityMetrics
    recommendation: ProductivityRecommendation
    warning: Optional[BurnoutWarning] = None

