from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AchievementBaseOut(BaseModel):
    title: str
    description: str

    class Config:
        from_attributes = True

class AchievementOut(BaseModel):
    title: str
    description: str
    unlocked: Optional[bool] = False
    unlocked_at: Optional[datetime] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True
