from fastapi import FastAPI
from app.api import tasks
from app.api.achievements import router as achievements_router
from app.api.auth import router as auth_router
from app.api.analytics import router as analytics_router

app = FastAPI(title="Main App")


app.include_router(achievements_router)
app.include_router(tasks.router)
app.include_router(auth_router)
app.include_router(analytics_router)


@app.get("/")
def root():
    return {"message": "Main API is running. See documentation at /docs"}
