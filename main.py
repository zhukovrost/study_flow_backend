from fastapi import FastAPI
from .routers.achievements import router as achievements_router, init_achievements

app = FastAPI(title="Main App")

@app.on_event("startup")
def startup_event():
    init_achievements()

app.include_router(achievements_router)

@app.get("/")
def root():
    return {"message": "Main API is running. See documentation at /docs"}
