"""
Функции для вычисления метрик продуктивности и риска выгорания
"""
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import math
import numpy as np


def sigmoid(x: float) -> float:
    """Сигмоидная функция"""
    return 1 / (1 + math.exp(-x))


def clip(value: float, min_val: float, max_val: float) -> float:
    """Ограничение значения в диапазоне"""
    return max(min_val, min(max_val, value))


def clean_data(daily_data: List[Dict]) -> List[Dict]:
    """
    Очистка данных:
    - пропуски = 0
    - удаление дубликатов
    - нормализация timezone
    """
    if not daily_data:
        return []
    
    # Удаление дубликатов по дате
    seen_dates = set()
    cleaned = []
    for record in daily_data:
        date = record['date']
        if isinstance(date, datetime):
            date_key = date.date()
        elif isinstance(date, str):
            date_key = datetime.fromisoformat(date.replace('Z', '+00:00')).date()
        else:
            date_key = date
        
        if date_key not in seen_dates:
            seen_dates.add(date_key)
            # Нормализуем дату к date объекту
            record_copy = record.copy()
            record_copy['date'] = date_key
            cleaned.append(record_copy)
    
    # Сортировка по дате
    cleaned.sort(key=lambda x: x['date'])
    
    # Заполнение пропусков нулями
    for record in cleaned:
        if record.get('tasks_done') is None:
            record['tasks_done'] = 0
        if record.get('streak') is None:
            record['streak'] = 0
    
    return cleaned


def calculate_weekday_productivity(daily_data: List[Dict]) -> Dict[int, float]:
    """
    Вычисление базовой продуктивности по дням недели
    Возвращает словарь {weekday: mean_tasks}, где weekday 0=Monday, 6=Sunday
    """
    from datetime import date as date_type
    weekday_tasks = defaultdict(list)
    
    for record in daily_data:
        date = record['date']
        if isinstance(date, datetime):
            weekday = date.weekday()
        elif isinstance(date, date_type):
            weekday = date.weekday()
        else:
            # Попытка преобразовать строку в дату
            try:
                if isinstance(date, str):
                    date_obj = datetime.fromisoformat(date.replace('Z', '+00:00')).date()
                else:
                    date_obj = date
                weekday = date_obj.weekday()
            except:
                continue
        tasks = record.get('tasks_done', 0)
        weekday_tasks[weekday].append(tasks)
    
    # Вычисление средних значений
    weekday_means = {}
    for weekday in range(7):
        if weekday in weekday_tasks:
            weekday_means[weekday] = np.mean(weekday_tasks[weekday])
        else:
            weekday_means[weekday] = 0.0
    
    return weekday_means


def normalize_seasonality(daily_data: List[Dict], weekday_means: Dict[int, float]) -> Tuple[List[float], Dict[int, float]]:
    """
    Нормализация сезонности
    Возвращает (adj_tasks_list, factors_dict)
    """
    if not daily_data:
        return [], {}
    
    # Вычисление общего среднего
    all_tasks = [r.get('tasks_done', 0) for r in daily_data]
    mu_all = np.mean(all_tasks) if all_tasks else 1.0
    
    # Вычисление факторов нормализации
    factors = {}
    epsilon = 0.1
    for weekday in range(7):
        mu_w = weekday_means.get(weekday, 0.0)
        if mu_all > epsilon:
            factors[weekday] = max(epsilon, mu_w / mu_all)
        else:
            factors[weekday] = 1.0
    
    # Применение нормализации
    from datetime import date as date_type
    adj_tasks = []
    for record in daily_data:
        date = record['date']
        if isinstance(date, datetime):
            weekday = date.weekday()
        elif isinstance(date, date_type):
            weekday = date.weekday()
        else:
            # Попытка преобразовать
            try:
                if isinstance(date, str):
                    date_obj = datetime.fromisoformat(date.replace('Z', '+00:00')).date()
                else:
                    date_obj = date
                weekday = date_obj.weekday()
            except:
                weekday = 0  # По умолчанию понедельник
        tasks = record.get('tasks_done', 0)
        factor = factors.get(weekday, 1.0)
        adj_tasks.append(tasks / factor)
    
    return adj_tasks, factors


def calculate_moving_averages(adj_tasks: List[float], window_7: int = 7, window_14: int = 14, window_28: int = 28) -> Dict[str, float]:
    """
    Вычисление скользящих средних
    """
    if not adj_tasks:
        return {
            'mean_7': 0.0,
            'mean_14': 0.0,
            'mean_28': 0.0,
            'std_28': 0.0
        }
    
    n = len(adj_tasks)
    
    # 7-дневное окно
    window_7_data = adj_tasks[-window_7:] if n >= window_7 else adj_tasks
    mean_7 = np.mean(window_7_data) if window_7_data else 0.0
    
    # 14-дневное окно
    window_14_data = adj_tasks[-window_14:] if n >= window_14 else adj_tasks
    mean_14 = np.mean(window_14_data) if window_14_data else 0.0
    
    # 28-дневное окно (базис)
    window_28_data = adj_tasks[-window_28:] if n >= window_28 else adj_tasks
    mean_28 = np.mean(window_28_data) if window_28_data else 0.0
    std_28 = np.std(window_28_data) if window_28_data else 0.0
    
    return {
        'mean_7': float(mean_7),
        'mean_14': float(mean_14),
        'mean_28': float(mean_28),
        'std_28': float(std_28)
    }


def calculate_ema(adj_tasks: List[float], alpha: float = 0.25) -> List[float]:
    """
    Экспоненциальное сглаживание
    """
    if not adj_tasks:
        return []
    
    ema_values = [adj_tasks[0]]
    for i in range(1, len(adj_tasks)):
        ema = alpha * adj_tasks[i] + (1 - alpha) * ema_values[-1]
        ema_values.append(ema)
    
    return ema_values


def calculate_z_score(adj_tasks_today: float, mean_28: float, std_28: float) -> float:
    """
    Вычисление z-score для текущего дня
    """
    if std_28 < 1.0:
        std_28 = 1.0
    if std_28 == 0:
        return 0.0
    return (adj_tasks_today - mean_28) / std_28


def calculate_burnout_components(
    adj_tasks: List[float],
    tasks_raw: List[int],
    streaks: List[int],
    ema_values: List[float],
    mean_28: float,
    mean_7: float
) -> Dict[str, float]:
    """
    Вычисление компонентов индекса риска выгорания
    """
    if not adj_tasks or not tasks_raw or not streaks or not ema_values:
        return {
            'downshift': 0.0,
            'momentum': 0.0,
            'zeros_rate': 0.0,
            'streak_strain': 0.0
        }
    
    # Downshift - падение короткого среднего к базису
    if mean_28 > 1.0:
        downshift = clip((mean_28 - mean_7) / mean_28, 0.0, 1.0)
    else:
        downshift = 0.0
    
    # Momentum - отрицательный импульс по EMA
    if len(ema_values) >= 2:
        ema_prev = ema_values[-2]
        ema_curr = ema_values[-1]
        if ema_prev > 1.0:
            momentum = clip((ema_prev - ema_curr) / ema_prev, 0.0, 1.0)
        else:
            momentum = 0.0
    else:
        momentum = 0.0
    
    # ZerosRate - доля нулевых дней в последней неделе
    last_7_tasks = tasks_raw[-7:] if len(tasks_raw) >= 7 else tasks_raw
    zeros_count = sum(1 for t in last_7_tasks if t == 0)
    zeros_rate = zeros_count / 7.0 if last_7_tasks else 0.0
    
    # StreakStrain - напряжение от длинного стрика
    current_streak = streaks[-1] if streaks else 0
    a = 0.35
    s0 = 7
    streak_strain = sigmoid(a * (current_streak - s0))
    
    return {
        'downshift': downshift,
        'momentum': momentum,
        'zeros_rate': zeros_rate,
        'streak_strain': streak_strain
    }


def calculate_burnout_risk_index(components: Dict[str, float]) -> Tuple[float, str]:
    """
    Вычисление индекса риска выгорания и категории
    """
    # Веса компонентов
    R_t = (
        0.35 * components['downshift'] +
        0.25 * components['momentum'] +
        0.25 * components['zeros_rate'] +
        0.15 * components['streak_strain']
    )
    R_t = clip(R_t, 0.0, 1.0)
    
    # Определение категории
    if R_t < 0.33:
        category = "низкий"
    elif R_t < 0.66:
        category = "средний"
    else:
        category = "высокий"
    
    return float(R_t), category


def get_top_weekdays(weekday_means: Dict[int, float], top_n: int = 2) -> List[Tuple[int, float]]:
    """
    Получить ТОП-N дней недели по продуктивности
    Возвращает список (weekday, mean_tasks) отсортированный по убыванию
    """
    weekday_names = {0: "Понедельник", 1: "Вторник", 2: "Среда", 3: "Четверг",
                     4: "Пятница", 5: "Суббота", 6: "Воскресенье"}
    
    sorted_weekdays = sorted(
        weekday_means.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    return sorted_weekdays[:top_n]


def calculate_productivity_metrics(daily_data: List[Dict]) -> Dict:
    """
    Основная функция для вычисления всех метрик продуктивности
    """
    # Очистка данных
    cleaned_data = clean_data(daily_data)
    
    if not cleaned_data:
        return {
            'weekday_productivity': {},
            'top_weekdays': [],
            'adj_tasks': [],
            'factors': {},
            'moving_averages': {},
            'ema_values': [],
            'z_score': 0.0
        }
    
    # Извлечение данных
    dates = [r['date'] for r in cleaned_data]
    tasks_raw = [r.get('tasks_done', 0) for r in cleaned_data]
    streaks = [r.get('streak', 0) for r in cleaned_data]
    
    # 1. Продуктивность по дням недели
    weekday_means = calculate_weekday_productivity(cleaned_data)
    
    # 2. Нормализация сезонности
    adj_tasks, factors = normalize_seasonality(cleaned_data, weekday_means)
    
    # 3. Скользящие средние
    moving_avgs = calculate_moving_averages(adj_tasks)
    
    # 4. EMA
    ema_values = calculate_ema(adj_tasks, alpha=0.25)
    
    # 5. Z-score для последнего дня
    z_score = 0.0
    if adj_tasks:
        z_score = calculate_z_score(
            adj_tasks[-1],
            moving_avgs['mean_28'],
            moving_avgs['std_28']
        )
    
    # 6. Компоненты риска выгорания
    components = calculate_burnout_components(
        adj_tasks,
        tasks_raw,
        streaks,
        ema_values,
        moving_avgs['mean_28'],
        moving_avgs['mean_7']
    )
    
    # 7. Индекс риска выгорания
    risk_index, risk_category = calculate_burnout_risk_index(components)
    
    # 8. ТОП-дни недели
    top_weekdays = get_top_weekdays(weekday_means, top_n=2)
    
    return {
        'weekday_productivity': {str(k): float(v) for k, v in weekday_means.items()},
        'top_weekdays': [{'weekday': w, 'mean_tasks': float(m)} for w, m in top_weekdays],
        'adj_tasks': [float(x) for x in adj_tasks],
        'factors': {str(k): float(v) for k, v in factors.items()},
        'moving_averages': moving_avgs,
        'ema_values': [float(x) for x in ema_values],
        'z_score': float(z_score),
        'burnout_risk': {
            'index': risk_index,
            'category': risk_category,
            'components': components
        },
        'dates': [d.isoformat() if isinstance(d, (datetime, date)) else str(d) for d in dates],
        'tasks_raw': tasks_raw,
        'streaks': streaks
    }


def calculate_burnout_risk(daily_data: List[Dict]) -> Dict:
    """
    Вычисление только индекса риска выгорания
    """
    metrics = calculate_productivity_metrics(daily_data)
    return metrics.get('burnout_risk', {'index': 0.0, 'category': 'низкий', 'components': {}})

