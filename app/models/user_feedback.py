"""
Модель для хранения ежедневных оценок пользователя
"""
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.database.base import Base


class UserDailyFeedback(Base):
    """
    Модель ежедневной оценки пользователя
    """
    __tablename__ = "user_daily_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)  # Дата оценки
    state = Column(String, nullable=False)  # Состояние: выгорел, устал, в норме, полон сил
    comment = Column(String, nullable=True)  # Опциональный комментарий
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", backref="daily_feedback")

