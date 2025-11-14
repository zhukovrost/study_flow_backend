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
    # If parent_id provided, ensure the parent exists and belongs to the same user
    parent_id = getattr(task, 'parent_id', None)
    if parent_id is not None:
        parent = db.query(Task).filter(Task.id == parent_id, Task.owner_id == user_id).first()
        if parent is None:
            raise ValueError('invalid_parent')
        # Subtasks cannot have a TaskList
        db_task = Task(
            title=task.title,
            description=task.description,
            due_date=task.due_date,
            scheduled_date=task.scheduled_date,
            priority=task.priority,
            owner_id=user_id,
            parent_id=parent_id,
            task_list_id=None
        )
    else:
        db_task = Task(
            title=task.title,
            description=task.description,
            due_date=task.due_date,
            scheduled_date=task.scheduled_date,
            priority=task.priority,
            owner_id=user_id,
            parent_id=None,
            task_list_id=getattr(task, 'task_list_id', None)
        )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task(db: Session, task_id: int, task: TaskUpdate, user_id: int) -> Optional[Task]:
    """Обновить задачу"""
    from datetime import datetime
    db_task = get_task(db, task_id, user_id)
    if not db_task:
        return None
    update_data = task.dict(exclude_unset=True)

    # Validate parent_id changes and enforce list rules for subtasks
    if 'parent_id' in update_data:
        new_parent_id = update_data.get('parent_id')
        if new_parent_id == task_id:
            raise ValueError('invalid_parent')
        if new_parent_id is not None:
            # Becoming/remaining a subtask
            parent = db.query(Task).filter(Task.id == new_parent_id, Task.owner_id == user_id).first()
            if parent is None:
                raise ValueError('invalid_parent')
            # Subtasks cannot have a TaskList
            update_data['task_list_id'] = None
        else:
            # Becoming root: allow task_list_id if provided
            pass
    else:
        # parent_id not changing; if currently a subtask, disallow changing task_list_id
        if db_task.parent_id is not None and 'task_list_id' in update_data:
            raise ValueError('invalid_list_for_subtask')

    # Helpers for recursive cascade
    def mark_completed_recursively(t: Task):
        t.is_completed = True
        if not t.completed_at:
            t.completed_at = datetime.utcnow()
        for st in t.subtasks:
            mark_completed_recursively(st)

    def mark_uncompleted_recursively(t: Task):
        t.is_completed = False
        t.completed_at = None
        for st in t.subtasks:
            mark_uncompleted_recursively(st)

    # Cascade completion to all subtasks recursively
    if update_data.get('is_completed') is True and not db_task.completed_at:
        update_data['completed_at'] = datetime.utcnow()
        mark_completed_recursively(db_task)
    elif update_data.get('is_completed') is False:
        update_data['completed_at'] = None
        mark_uncompleted_recursively(db_task)

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
    """Отметить задачу как выполненную (каскадно для подзадач)"""
    from datetime import datetime
    db_task = get_task(db, task_id, user_id)
    if not db_task:
        return None
    def mark_completed(task: Task):
        task.is_completed = True
        if not task.completed_at:
            task.completed_at = datetime.utcnow()
        for subtask in task.subtasks:
            mark_completed(subtask)
    mark_completed(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task
