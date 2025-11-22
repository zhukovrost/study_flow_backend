"""
API endpoints для списков задач
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.base import get_db
from app.models.user import User
from app.schemas.list import TaskList, TaskListCreate, TaskListUpdate
from app.schemas.task import Task as TaskSchema
from app import crud
from app.deps import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[TaskList])
def get_lists(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """
    Получить список всех списков задач текущего пользователя
    """
    return crud.get_lists(db, user_id=current_user.id, skip=skip, limit=limit)


@router.post("/", response_model=TaskList, status_code=status.HTTP_201_CREATED)
def create_list(task_list: TaskListCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """
    Создать новый список задач (owner = current user)
    """
    existing = crud.get_list_by_name(db, name=task_list.name, user_id=current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="List with this name already exists"
        )
    return crud.create_list(db=db, name=task_list.name, creator_id=current_user.id)


@router.get("/{list_id}", response_model=TaskList)
def get_list(list_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """
    Получить список по ID (только если вы его создали)
    """
    db_list = crud.get_list(db, list_id=list_id, user_id=current_user.id)
    if db_list is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    return db_list


@router.put("/{list_id}", response_model=TaskList)
def update_list(list_id: int, task_list: TaskListUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """
    Обновить список (только создатель)
    """
    db_list = crud.update_list(db=db, list_id=list_id, task_list=task_list, user_id=current_user.id)
    if db_list is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    return db_list


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(list_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """
    Удалить список (только создатель)
    """
    success = crud.delete_list(db=db, list_id=list_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")


# --- endpoints to manage tasks in a list ---


@router.get("/{list_id}/tasks", response_model=List[TaskSchema])
def get_tasks_in_list(list_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """
    Получить задачи (корневые) в списке (только если вы создатель списка)
    """
    tasks = crud.get_tasks_in_list(db=db, list_id=list_id, user_id=current_user.id)
    if tasks is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    return tasks


@router.post("/{list_id}/tasks", status_code=status.HTTP_201_CREATED)
def add_task_to_list(list_id: int, task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """
    Добавить корневую задачу в список (body/query: task_id как int) только для создателя списка
    """
    added = crud.add_task_to_list(db=db, list_id=list_id, task_id=task_id, user_id=current_user.id)
    if not added:
        if crud.get_list(db, list_id=list_id, user_id=current_user.id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not add task to list")
    return {"detail": "Task added to list"}


@router.delete("/{list_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_task_from_list(list_id: int, task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """
    Удалить корневую задачу из списка (только создатель)
    """
    if crud.get_list(db, list_id=list_id, user_id=current_user.id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    removed = crud.remove_task_from_list(db=db, list_id=list_id, task_id=task_id, user_id=current_user.id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found in list")