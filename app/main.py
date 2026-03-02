from fastapi import FastAPI

from routers.auth import router as auth_router
from routers.models import router as models_router

app = FastAPI(title="Model Registry")

app.include_router(auth_router)
app.include_router(models_router)

@app.get("/")
def root():
    return {"status": "ok"}