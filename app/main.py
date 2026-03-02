from fastapi import FastAPI

from routers.auth import router as auth_router
from routers.models import router as models_router
from routers.versions import router as versions_router
from services.storage import ensure_bucket

app = FastAPI(title="Model Registry")

app.include_router(auth_router)
app.include_router(models_router)
app.include_router(versions_router)


@app.on_event("startup")
def startup():
    ensure_bucket()

@app.get("/")
def root():
    return {"status": "ok"}