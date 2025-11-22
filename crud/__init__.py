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
from .list import (
    get_list,
    get_lists,
    get_list_by_name,
    create_list,
    update_list,
    delete_list,
    get_tasks_in_list,
    add_task_to_list,
    remove_task_from_list
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
    "get_list",
    "get_lists",
    "get_list_by_name",
    "create_list",
    "update_list",
    "delete_list",
    "get_tasks_in_list",
    "add_task_to_list",
    "remove_task_from_list"
]