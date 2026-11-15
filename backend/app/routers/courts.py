from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_user, profiled_user
from ..models import Court, User
from ..schemas import CourtIn, CourtOut
from ..services import court_out, favorite_ids

router = APIRouter(prefix="/courts", tags=["courts"])


@router.get("", response_model=list[CourtOut])
def list_courts(
    sport: str | None = None,
    q: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    user: User = Depends(get_user),
    db: Session = Depends(get_db),
):
    stmt = select(Court)
    if sport:
        stmt = stmt.where(Court.sport == sport)
    if q:
        stmt = stmt.where(Court.name.ilike(f"%{q}%"))
    favs = favorite_ids(db, user.id)
    out = [court_out(c, favs, lat, lng) for c in db.scalars(stmt.limit(300))]
    out.sort(key=lambda c: (c["distance_mi"] is None, c["distance_mi"] or 0, c["name"]))
    return out


@router.post("", response_model=CourtOut, status_code=201)
def create_court(body: CourtIn, user: User = Depends(profiled_user), db: Session = Depends(get_db)):
    court = Court(**body.model_dump(), created_by=user.id)
    db.add(court)
    db.commit()
    return court_out(court, favorite_ids(db, user.id))


@router.get("/{court_id}", response_model=CourtOut)
def get_court(court_id: int, user: User = Depends(get_user), db: Session = Depends(get_db)):
    court = db.get(Court, court_id)
    if not court:
        raise HTTPException(404, "Court not found")
    return court_out(court, favorite_ids(db, user.id))
