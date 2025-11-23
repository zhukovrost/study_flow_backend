from fastapi import APIRouter, Depends, Body, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.database.base import get_db, Base, engine
from app.models.user import User
from app.models.achievements import Achievement, UserAchievement
from app.schemas.achievements import AchievementOut

router = APIRouter(prefix="/achievements", tags=["Achievements"])

def init_achievements():
    Base.metadata.create_all(bind=engine)
    db: Session = next(get_db())
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

    # Удалено создание тестового пользователя - пользователи создаются через API регистрации
    db.close()


def check_achievements(user: User, db: Session) -> None:
    """Проверяет и разблокирует достижения пользователя"""
    for ach in db.query(Achievement).all():
        cond_attr = str(ach.condition_type)  # Преобразуем Column в строку
        # Получаем значение атрибута пользователя
        value = getattr(user, cond_attr, None)
        if value is None:
            continue
        ua = db.query(UserAchievement).filter_by(user_id=user.id, achievement_id=ach.id).first()
        if not ua:
            ua = UserAchievement(user_id=user.id, achievement_id=ach.id)
            db.add(ua)
        # Проверяем и обновляем статус разблокировки
        if not bool(ua.unlocked) and isinstance(value, (int, float)) and value >= ach.condition_value:
            ua.unlocked = True  # type: ignore
            ua.unlocked_at = datetime.now()  # type: ignore
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    user.completed_goals += 1
    db.add(user)  # Ensure the user object is in the session and marked as dirty
    check_achievements(user, db)
    db.commit()
    db.refresh(user)
    return {"message": "Goal completed", "completed_goals": user.completed_goals}

@router.post("/users/{user_id}/streak", response_model=dict)
def update_streak(user_id: int, streak: int = Body(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    user.streak_days = streak
    db.add(user)  # Ensure the user object is in the session and marked as dirty
    check_achievements(user, db)
    db.commit()
    db.refresh(user)
    return {"message": "Streak updated", "streak_days": user.streak_days}
