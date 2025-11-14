# python
# file: app/models/list.py

from sqlalchemy import Column, Integer, String, ForeignKey
from app.database.base import Base


class TaskList(Base):
    """
    Model for a task list.
    """
    __tablename__ = "task_lists"

    id = Column(Integer, primary_key=True, index=True)
    # name should not be globally unique so multiple users can have lists with the same name
    name = Column(String, unique=False, nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
