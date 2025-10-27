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
    due_date = Column(DateTime, nullable=True)
    scheduled_date = Column(DateTime, nullable=True)  # Планируемая дата выполнения
    
    # Связь с пользователем
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", backref="tasks")
    
    # Связь с категорией
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category = relationship("Category", backref="tasks")
    
    # Дополнительные поля для StudyFlow
    priority = Column(Integer, default=1)  # 1 - низкая, 2 - средняя, 3 - высокая





