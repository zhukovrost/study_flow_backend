from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import List

from app.database import get_db, Base, engine
from app.models.achievements import Achievement, UserAchievement
from app.models.user import User
from app.schemas.achievements import AchievementOut

router = APIRouter()

# -------------------------------------------
#  Initialize Achievements (added 7 more)
# -------------------------------------------

def init_achievements():
    Base.metadata.create_all(bind=engine)
    db: Session = next(get_db())
    try:
        if not db.query(Achievement).first():
            demo = [
                Achievement(code="welcome", title="Добро пожаловать!", description="Зайди в приложение",
                            condition_type="login_days", condition_value=1),
                Achievement(code="first_goal", title="Первая цель!", description="Выполни первую учебную цель",
                            condition_type="completed_goals", condition_value=1),
                Achievement(code="goals_3", title="Первые шаги", description="Выполни 3 цели",
                            condition_type="completed_goals", condition_value=3),
                Achievement(code="goal_master", title="Настойчивость", description="Выполни 10 целей",
                            condition_type="completed_goals", condition_value=10),
                Achievement(code="streak_3", title="3 дня подряд", description="Учись 3 дня подряд",
                            condition_type="streak_days", condition_value=3),
                Achievement(code="streak_7", title="7 дней подряд", description="Учись 7 дней без перерыва",
                            condition_type="streak_days", condition_value=7),
                Achievement(code="streak_30", title="Месяц учёбы", description="Учись 30 дней подряд",
                            condition_type="streak_days", condition_value=30),
                Achievement(code="goals_20", title="20 целей!", description="Серьёзный прогресс",
                            condition_type="completed_goals", condition_value=20),
                Achievement(code="goals_50", title="50 целей!", description="Отличная работа",
                            condition_type="completed_goals", condition_value=50),
                Achievement(code="consistency_15", title="Постоянство", description="Учись 15 дней в этом месяце",
                            condition_type="month_active_days", condition_value=15)
            ]
            db.add_all(demo)
            db.commit()
    finally:
        db.close()


def handle_user_login(user, db):
    today = date.today()

    # Первый вход
    if user.last_login_date is None:
        user.last_login_date = today
        user.login_days = 1
        user.streak_days = 1
    else:

        if user.last_login_date == today - timedelta(days=1):
            user.streak_days += 1

        elif user.last_login_date != today:
            user.streak_days = 1


        if user.last_login_date != today:
            user.login_days += 1

        user.last_login_date = today

    db.commit()
    db.refresh(user)

    return user

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


def update_streak(user: User):
    today = date.today()

    if user.last_login_date is None:
        user.streak_days = 1
    else:
        if user.last_login_date == today - timedelta(days=1):
            user.streak_days += 1
        elif user.last_login_date == today:
            pass
        else:
            user.streak_days = 1

    user.last_login_date = today


@router.post("/users/{user_id}/login", response_model=dict)
def user_login(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, name=f"user{user_id}")
        db.add(user)
        db.commit()
        db.refresh(user)

    update_streak(user)

    user.login_days = (user.login_days or 0) + 1

    check_achievements(user, db)
    db.commit()

    return {"message": "User logged in", "streak_days": user.streak_days}


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
