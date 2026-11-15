from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import settings
from .db import Base, engine
from .routers import auth, courts, games, invites, leagues, me, users

Base.metadata.create_all(engine)
Path(settings.upload_dir, "avatars").mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Pickup API")

for module in (auth, me, users, courts, games, leagues, invites):
    app.include_router(module.router, prefix="/api")

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/api/health")
def health():
    return {"ok": True}
