from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.database import get_db, Base, engine
from app.models.achievements import Achievement, UserAchievement
from app.models.user import User
from app.schemas.achievements import AchievementOut

router = APIRouter()

def init_achievements():
    Base.metadata.create_all(bind=engine)
    db: Session = next(get_db())
    try:
        if not db.query(Achievement).first():
            demo = [
                Achievement(code="first_goal", title="Первая цель!", description="Выполни первую учебную цель",
                            condition_type="completed_goals", condition_value=1),
                Achievement(code="goal_master", title="Настойчивость", description="Выполни 10 целей",
                            condition_type="completed_goals", condition_value=10),
                Achievement(code="streak_7", title="7 дней подряд", description="Учись 7 дней без перерыва",
                            condition_type="streak_days", condition_value=7)
            ]
            db.add_all(demo)
            db.commit()
    finally:
        db.close()

def check_achievements(user: User, db: Session) -> None:
    for ach in db.query(Achievement).all():
        cond_attr = ach.condition_type
        value = getattr(user, cond_attr, None)
        if value is None:
            continue
        ua = db.query(UserAchievement).filter_by(user_id=user.id, achievement_id=ach.id).first()
        if not ua:
            ua = UserAchievement(user_id=user.id, achievement_id=ach.id)
            db.add(ua)
        if not ua.unlocked and value >= ach.condition_value:
            ua.unlocked = True
            ua.unlocked_at = datetime.now()
    db.commit()

@router.get("/", response_model=List[AchievementOut])
def get_all_achievements(db: Session = Depends(get_db)):
    return db.query(Achievement).all()


@router.get("/users/{user_id}", response_model=List[AchievementOut])
def get_user_achievements(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []
    ua_list = db.query(UserAchievement).filter(UserAchievement.user_id == user.id).all()
    result = []
    for ua in ua_list:
        ach = ua.achievement
        data = {
            "title": ach.title,
            "description": ach.description,
            "unlocked": ua.unlocked,
            "unlocked_at": ua.unlocked_at,
        }
        result.append(AchievementOut(**data))
    return result


@router.post("/users/{user_id}/goal_completed", response_model=dict)
def complete_goal(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, name=f"user{user_id}")
        db.add(user)
        db.commit()
        db.refresh(user)
    user.completed_goals += 1
    check_achievements(user, db)
    db.commit()
    return {"message": "Goal completed", "completed_goals": user.completed_goals}

@router.post("/users/{user_id}/streak", response_model=dict)
def update_streak(user_id: int, streak: int = Body(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, name=f"user{user_id}")
        db.add(user)
        db.commit()
        db.refresh(user)
    user.streak_days = streak
    check_achievements(user, db)
    db.commit()
    return {"message": "Streak updated", "streak_days": user.streak_days}
