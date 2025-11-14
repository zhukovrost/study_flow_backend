# python
# file: app/schemas/list.py

from pydantic import BaseModel
from typing import Optional


class TaskListBase(BaseModel):
    """Base schema for a task list."""
    name: str


class TaskListCreate(TaskListBase):
    """Schema for creating a task list.
    Creator is determined from the authenticated user, not provided by client.
    """


class TaskListUpdate(BaseModel):
    """Schema for updating a task list."""
    name: Optional[str] = None


class TaskList(TaskListBase):
    """Public schema for a task list."""
    id: int
    creator_id: int

    class Config:
        from_attributes = True
