from fastapi import FastAPI

from routers.auth import router as auth_router

app = FastAPI(title="Model Registry")

app.include_router(auth_router)

@app.get("/")
def root():
    return {"status": "ok"}