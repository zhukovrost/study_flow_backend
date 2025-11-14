"""
Модель задачи
"""
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.base import Base


class Task(Base):
    """
    Модель задачи
    """
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)  # Дата завершения задачи
    due_date = Column(DateTime, nullable=True)
    scheduled_date = Column(DateTime, nullable=True)  # Планируемая дата выполнения
    
    # Связь с пользователем
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", backref="tasks")

    # Self-referential parent/children for subtasks
    parent_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)
    parent = relationship("Task", remote_side=[id], backref="subtasks")

    # Дополнительные поля для StudyFlow
    priority = Column(Integer, default=1)  # 1 - низкая, 2 - средняя, 3 - высокая

    # Only root tasks can belong to a TaskList
    task_list_id = Column(Integer, ForeignKey("task_lists.id", ondelete="SET NULL"), nullable=True)
    task_list = relationship("TaskList", backref="tasks")
