from fastapi import FastAPI
import subprocess
import sys
import logging

logger = logging.getLogger(__name__)

def ensure_google_ai_installed():
    """Проверяет и автоматически устанавливает google-generativeai если необходимо"""
    try:
        import google.generativeai  # type: ignore
        logger.info("google-generativeai уже установлен")
        return True
    except ImportError:
        logger.warning("google-generativeai не найден, пытаюсь установить...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "google-generativeai"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info("google-generativeai успешно установлен")
            return True
        except subprocess.CalledProcessError:
            logger.error("Не удалось автоматически установить google-generativeai. Установите вручную: pip install google-generativeai")
            return False

from app.routers.achievements import router as achievements_router, init_achievements
from app.api import auth, tasks, list, analytics, subtasks

app = FastAPI(title="StudyFlow API", version="1.0.0")

@app.on_event("startup")
def startup_event():
    # Автоматическая установка google-generativeai если необходимо
    ensure_google_ai_installed()
    # Инициализация достижений
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

