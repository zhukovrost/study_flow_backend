"""
Инициализация CRUD модуля с экспортом функций
"""
from .user import (
    get_user,
    get_user_by_email,
    get_user_by_username,
    create_user,
    update_user,
    authenticate_user
)
from .task import (
    get_task,
    get_tasks,
    create_task,
    update_task,
    delete_task,
    complete_task
)
from .category import (
    get_category,
    get_categories,
    get_category_by_name,
    create_category,
    update_category,
    delete_category
)

__all__ = [
    "get_user",
    "get_user_by_email",
    "get_user_by_username",
    "create_user",
    "update_user",
    "authenticate_user",
    "get_task",
    "get_tasks",
    "create_task",
    "update_task",
    "delete_task",
    "complete_task",
    "get_category",
    "get_categories",
    "get_category_by_name",
    "create_category",
    "update_category",
    "delete_category",
]
