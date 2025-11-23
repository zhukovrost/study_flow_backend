"""
Pydantic схемы для подзадач, созданных с помощью AI
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class SubtaskBreakdown(BaseModel):
    """Схема одной подзадачи из разбиения"""
    id: str = Field(..., description="Идентификатор подзадачи (s1, s2, ...)")
    title: str = Field(..., description="Краткий заголовок подзадачи")
    description: str = Field(..., description="Описание того, что нужно сделать")
    acceptance_criteria: List[str] = Field(default_factory=list, description="Критерии приемки")
    priority: str = Field(..., description="Приоритет: high, medium, low")
    estimated_effort: int = Field(..., ge=1, le=5, description="Оценка усилий от 1 до 5")
    dependencies: List[str] = Field(default_factory=list, description="ID зависимых подзадач")


class TaskBreakdownRequest(BaseModel):
    """Запрос на разбиение задачи"""
    task_description: str = Field(..., description="Описание задачи на естественном языке")
    context: Optional[str] = Field(None, description="Дополнительный контекст")
    constraints: Optional[str] = Field(None, description="Ограничения (дедлайны, технологии, ресурсы)")


class TaskBreakdownResponse(BaseModel):
    """Ответ с разбиением задачи на подзадачи"""
    version: str = Field(..., description="Версия формата")
    input_task: str = Field(..., description="Исходная задача")
    subtasks: List[SubtaskBreakdown] = Field(..., description="Список подзадач")


class CreateSubtasksRequest(BaseModel):
    """Запрос на создание подзадач из разбиения"""
    parent_task_id: int = Field(..., description="ID родительской задачи")
    subtasks: List[SubtaskBreakdown] = Field(..., description="Список подзадач для создания")


