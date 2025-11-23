"""
API endpoints для разбиения задач на подзадачи с помощью AI
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.database.base import get_db
from app.models.user import User
from app.models.task import Task
from app.deps import get_current_active_user
from app.schemas.subtask import (
    TaskBreakdownRequest,
    TaskBreakdownResponse,
    CreateSubtasksRequest,
    SubtaskBreakdown
)
from app.schemas.task import Task as TaskSchema
from app.services.ai_service import create_task_breakdown_service
from app import crud

router = APIRouter()


@router.post("/breakdown", response_model=TaskBreakdownResponse)
def break_down_task(
    request: TaskBreakdownRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Разбить задачу на подзадачи с помощью AI
    
    Возвращает разбиение задачи на 3-5 подзадач с описаниями,
    критериями приемки, приоритетами и зависимостями.
    """
    # Создаем сервис разбиения задач
    breakdown_service = create_task_breakdown_service()
    
    if breakdown_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис разбиения задач недоступен. Проверьте настройку YANDEXGPT_API_KEY и YANDEXGPT_FOLDER_ID."
        )
    
    try:
        # Разбиваем задачу
        result = breakdown_service.break_down_task(
            task_description=request.task_description,
            context=request.context,
            constraints=request.constraints
        )
        
        return TaskBreakdownResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при разбиении задачи: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обращении к AI сервису: {str(e)}"
        )


@router.post("/{task_id}/breakdown", response_model=TaskBreakdownResponse)
def break_down_existing_task(
    task_id: int,
    context: str = None,
    constraints: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Разбить существующую задачу на подзадачи
    
    Использует описание существующей задачи для разбиения.
    """
    # Получаем задачу
    task = crud.get_task(db, task_id=task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )
    
    # Создаем сервис разбиения задач
    breakdown_service = create_task_breakdown_service()
    
    if breakdown_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис разбиения задач недоступен. Проверьте настройку YANDEXGPT_API_KEY и YANDEXGPT_FOLDER_ID."
        )
    
    try:
        # Формируем описание задачи
        task_description = task.title
        if task.description:
            task_description += f". {task.description}"
        
        # Разбиваем задачу
        result = breakdown_service.break_down_task(
            task_description=task_description,
            context=context,
            constraints=constraints
        )
        
        return TaskBreakdownResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при разбиении задачи: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обращении к AI сервису: {str(e)}"
        )


@router.post("/{task_id}/create-subtasks", response_model=List[TaskSchema])
def create_subtasks_from_breakdown(
    task_id: int,
    request: CreateSubtasksRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Создать подзадачи из разбиения
    
    Создает подзадачи на основе результата разбиения задачи AI.
    Все подзадачи будут связаны с указанной родительской задачей.
    """
    # Проверяем, что родительская задача существует и принадлежит пользователю
    parent_task = crud.get_task(db, task_id=task_id, user_id=current_user.id)
    if not parent_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Родительская задача не найдена"
        )
    
    # Проверяем, что task_id совпадает
    if request.parent_task_id != task_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID родительской задачи в запросе не совпадает с ID в URL"
        )
    
    created_tasks = []
    
    # Создаем подзадачи в порядке их зависимостей
    # Сначала создаем подзадачи без зависимостей
    subtasks_by_id = {st.id: st for st in request.subtasks}
    created_subtask_ids = {}
    
    def can_create_subtask(subtask: SubtaskBreakdown) -> bool:
        """Проверяет, можно ли создать подзадачу (все зависимости созданы)"""
        if not subtask.dependencies:
            return True
        return all(dep_id in created_subtask_ids for dep_id in subtask.dependencies)
    
    # Создаем подзадачи
    remaining = list(request.subtasks)
    max_iterations = len(request.subtasks) * 2  # Защита от бесконечного цикла
    
    while remaining and max_iterations > 0:
        max_iterations -= 1
        created_in_iteration = []
        
        for subtask in remaining[:]:
            if can_create_subtask(subtask):
                # Преобразуем приоритет AI в числовой формат
                priority_map = {"high": 3, "medium": 2, "low": 1}
                priority = priority_map.get(subtask.priority.lower(), 2)
                
                # Формируем описание с критериями приемки
                description = subtask.description
                if subtask.acceptance_criteria:
                    description += "\n\nКритерии приемки:\n" + "\n".join(
                        f"- {criterion}" for criterion in subtask.acceptance_criteria
                    )
                
                # Создаем подзадачу
                from app.schemas.task import TaskCreate
                task_create = TaskCreate(
                    title=subtask.title,
                    description=description,
                    priority=priority,
                    parent_id=task_id
                )
                
                created_task = crud.create_task(
                    db=db,
                    task=task_create,
                    user_id=current_user.id
                )
                
                created_tasks.append(created_task)
                created_subtask_ids[subtask.id] = created_task.id
                created_in_iteration.append(subtask)
                remaining.remove(subtask)
        
        if not created_in_iteration:
            # Если не удалось создать ни одной подзадачи, возможно есть циклические зависимости
            logger.warning(f"Не удалось создать подзадачи. Оставшиеся: {[st.id for st in remaining]}")
            break
    
    if remaining:
        # Создаем оставшиеся подзадачи без учета зависимостей
        for subtask in remaining:
            priority_map = {"high": 3, "medium": 2, "low": 1}
            priority = priority_map.get(subtask.priority.lower(), 2)
            
            description = subtask.description
            if subtask.acceptance_criteria:
                description += "\n\nКритерии приемки:\n" + "\n".join(
                    f"- {criterion}" for criterion in subtask.acceptance_criteria
                )
            
            from app.schemas.task import TaskCreate
            task_create = TaskCreate(
                title=subtask.title,
                description=description,
                priority=priority,
                parent_id=task_id
            )
            
            created_task = crud.create_task(
                db=db,
                task=task_create,
                user_id=current_user.id
            )
            
            created_tasks.append(created_task)
    
    return created_tasks

