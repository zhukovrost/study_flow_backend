"""
CRUD операции для задач
"""
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


def get_task(db: Session, task_id: int, user_id: int) -> Optional[Task]:
    """Получить задачу по ID"""
    return db.query(Task).filter(Task.id == task_id, Task.owner_id == user_id).first()


def get_tasks(db: Session, user_id: int, skip: int = 0, limit: int = 100, 
              is_completed: Optional[bool] = None) -> List[Task]:
    """Получить список задач пользователя"""
    query = db.query(Task).filter(Task.owner_id == user_id)
    
    if is_completed is not None:
        query = query.filter(Task.is_completed == is_completed)
    
    return query.offset(skip).limit(limit).all()


def create_task(db: Session, task: TaskCreate, user_id: int) -> Task:
    """Создать новую задачу"""
    db_task = Task(
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        scheduled_date=task.scheduled_date,
        priority=task.priority,
        category_id=task.category_id,
        owner_id=user_id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task(db: Session, task_id: int, task: TaskUpdate, user_id: int) -> Optional[Task]:
    """Обновить задачу"""
    db_task = get_task(db, task_id, user_id)
    if not db_task:
        return None
    
    update_data = task.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int, user_id: int) -> bool:
    """Удалить задачу"""
    db_task = get_task(db, task_id, user_id)
    if not db_task:
        return False
    
    db.delete(db_task)
    db.commit()
    return True


def complete_task(db: Session, task_id: int, user_id: int) -> Optional[Task]:
    """Отметить задачу как выполненную"""
    db_task = get_task(db, task_id, user_id)
    if not db_task:
        return None
    
    db_task.is_completed = True
    db.commit()
    db.refresh(db_task)
    return db_task





