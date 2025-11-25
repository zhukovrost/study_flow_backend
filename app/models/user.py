"""
Модель пользователя
"""
from typing import Optional
from sqlalchemy import Boolean, Column, Integer, String, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class User(Base):
    """
    Модель пользователя
    """
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    surname: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    achievements = relationship("UserAchievement", back_populates="user")
    completed_goals = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    last_login_date = Column(Date, nullable=True)
    login_days = Column(Integer, default=0)
