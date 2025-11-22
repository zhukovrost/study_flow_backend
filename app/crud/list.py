from sqlalchemy.orm import Session
from app.models.list import TaskList as TaskListModel
from app.schemas.list import TaskListUpdate
from app.models.task import Task


def get_lists(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """
    Retrieve task lists owned by a specific user with optional pagination.
    """
    return (
        db.query(TaskListModel)
        .filter(TaskListModel.creator_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_list(db: Session, list_id: int, user_id: int):
    """
    Retrieve a task list by its ID only if it belongs to the given user.
    """
    return (
        db.query(TaskListModel)
        .filter(TaskListModel.id == list_id, TaskListModel.creator_id == user_id)
        .first()
    )


def get_list_by_name(db: Session, name: str, user_id: int):
    """
    Retrieve a task list by its name for a specific user.
    """
    return (
        db.query(TaskListModel)
        .filter(TaskListModel.name == name, TaskListModel.creator_id == user_id)
        .first()
    )


def create_list(db: Session, name: str, creator_id: int):
    """
    Create a new task list owned by creator_id.
    """
    db_task_list = TaskListModel(name=name, creator_id=creator_id)
    db.add(db_task_list)
    db.commit()
    db.refresh(db_task_list)
    return db_task_list


def update_list(db: Session, list_id: int, task_list: TaskListUpdate, user_id: int):
    """
    Update an existing task list if it belongs to the user.
    """
    db_task_list = get_list(db, list_id, user_id)
    if not db_task_list:
        return None
    for key, value in task_list.dict(exclude_unset=True).items():
        setattr(db_task_list, key, value)
    db.commit()
    db.refresh(db_task_list)
    return db_task_list


def delete_list(db: Session, list_id: int, user_id: int):
    """
    Delete a task list by its ID if it belongs to the user.
    """
    db_task_list = get_list(db, list_id, user_id)
    if not db_task_list:
        return False
    db.delete(db_task_list)
    db.commit()
    return True


def get_tasks_in_list(db: Session, list_id: int, user_id: int):
    """
    Retrieve all root tasks in a specific task list if the list belongs to the user.
    Returns full Task objects (not IDs).
    """
    if get_list(db, list_id, user_id) is None:
        return None
    return db.query(Task).filter(
        Task.task_list_id == list_id,
        Task.owner_id == user_id,
        Task.parent_id == None
    ).all()


def add_task_to_list(db: Session, list_id: int, task_id: int, user_id: int):
    """
    Add a root task to a task list if the list belongs to the user.
    Subtasks cannot belong to lists.
    """
    if get_list(db, list_id, user_id) is None:
        return False
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == user_id).first()
    if not task or task.parent_id is not None:
        return False
    task.task_list_id = list_id
    db.commit()
    return True


def remove_task_from_list(db: Session, list_id: int, task_id: int, user_id: int):
    """
    Remove a root task from a task list if the list belongs to the user.
    """
    if get_list(db, list_id, user_id) is None:
        return False
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == user_id).first()
    if not task or task.task_list_id != list_id:
        return False
    task.task_list_id = None
    db.commit()
    return True


def get_list_tasks(db: Session, list_id: int, user_id: int):
    """
    Получить список корневых задач (и их подзадач) для TaskList
    """
    # Only root tasks (parent_id is None) belonging to this list and user
    return db.query(Task).filter(
        Task.task_list_id == list_id,
        Task.owner_id == user_id,
        Task.parent_id == None
    ).all()
