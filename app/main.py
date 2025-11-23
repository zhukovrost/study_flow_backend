from fastapi import FastAPI
import subprocess
import sys
import logging

logger = logging.getLogger(__name__)

from app.routers.achievements import router as achievements_router, init_achievements
from app.api import auth, tasks, list, analytics, subtasks

app = FastAPI(title="StudyFlow API", version="1.0.0")

@app.on_event("startup")
def startup_event():
    init_achievements()

# Include routers
app.include_router(achievements_router)
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(list.router, prefix="/api/v1/tasklists", tags=["Task Lists"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(subtasks.router, prefix="/api/v1/subtasks", tags=["Task Breakdown"])

@app.get("/")
def root():
    return {"message": "StudyFlow API is running. See documentation at /docs"}

