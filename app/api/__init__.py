# API module
"""
Инициализация Achievements модуля с экспортом функций
"""

from .achievements import (
    get_all_achievements,
    get_user_achievements,
    complete_goal,
    update_streak,
    init_achievements,
    check_achievements
)

__all__ = [
    "get_all_achievements",
    "get_user_achievements",
    "complete_goal",
    "update_streak",
    "init_achievements",
    "check_achievements"
]
