from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import SessionRow, User, utcnow
from .security import digest

COOKIE = "session"


def get_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE)
    if not token:
        raise HTTPException(401, "Not signed in")
    row = db.scalar(
        select(SessionRow).where(
            SessionRow.token_hash == digest(token), SessionRow.expires_at > utcnow()
        )
    )
    if not row or row.user.status != "active":
        raise HTTPException(401, "Not signed in")
    return row.user


def verified_user(user: User = Depends(get_user)) -> User:
    if not user.email_verified_at:
        raise HTTPException(403, "Verify your email first")
    return user


def profiled_user(user: User = Depends(verified_user)) -> User:
    if not user.profile:
        raise HTTPException(403, "Finish your profile first")
    return user
