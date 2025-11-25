from fastapi import FastAPI
from app.api import tasks
from app.api.achievements import router as achievements_router
from app.api.auth import router as auth_router
from app.api.analytics import router as analytics_router
from app.database.base import engine
from app.database.base import Base
from app.api import achievements

app = FastAPI(title="Main App")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    achievements.init_achievements()

app.include_router(achievements_router, prefix="/achievements")
app.include_router(tasks.router)
app.include_router(auth_router, prefix="/auth")
app.include_router(analytics_router)

@app.get("/")
def root():
    return {"message": "Main API is running. See documentation at /docs"}
