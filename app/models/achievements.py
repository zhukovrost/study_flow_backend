from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database.base import Base

class Achievement(Base):
    __tablename__ = "achievements"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True)
    title = Column(String)
    description = Column(String)
    condition_type = Column(String)
    condition_value = Column(Integer)
    users = relationship("UserAchievement", back_populates="achievement")

class UserAchievement(Base):
    __tablename__ = "user_achievements"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    achievement_id = Column(Integer, ForeignKey("achievements.id"))
    unlocked = Column(Boolean, default=False)
    unlocked_at = Column(DateTime, nullable=True)
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="users")
