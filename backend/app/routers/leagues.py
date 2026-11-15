from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import profiled_user
from ..models import Court, League, LeagueMember, User
from ..schemas import LeagueIn, LeagueOut
from ..services import league_out

router = APIRouter(prefix="/leagues", tags=["leagues"])


@router.get("", response_model=list[LeagueOut])
def list_leagues(
    court_id: int | None = None,
    organizing: bool = False,
    user: User = Depends(profiled_user),
    db: Session = Depends(get_db),
):
    stmt = select(League)
    if court_id:
        stmt = stmt.where(League.court_id == court_id)
    if organizing:
        stmt = stmt.where(League.organizer_id == user.id)
    return [league_out(x, user.id) for x in db.scalars(stmt.order_by(League.name).limit(200))]


@router.post("", response_model=LeagueOut, status_code=201)
def create_league(body: LeagueIn, user: User = Depends(profiled_user), db: Session = Depends(get_db)):
    if not db.get(Court, body.court_id):
        raise HTTPException(404, "Court not found")
    league = League(court_id=body.court_id, organizer_id=user.id, name=body.name, weekday=body.weekday, time=body.time, skill=body.skill)
    db.add(league)
    db.flush()
    db.add(LeagueMember(league_id=league.id, user_id=user.id))
    db.commit()
    db.refresh(league)
    return league_out(league, user.id)


def load(db: Session, league_id: int) -> League:
    league = db.get(League, league_id)
    if not league:
        raise HTTPException(404, "League not found")
    return league


@router.post("/{league_id}/join", response_model=LeagueOut)
def join(league_id: int, user: User = Depends(profiled_user), db: Session = Depends(get_db)):
    league = load(db, league_id)
    if not db.get(LeagueMember, (league.id, user.id)):
        db.add(LeagueMember(league_id=league.id, user_id=user.id))
        db.commit()
        db.refresh(league)
    return league_out(league, user.id)


@router.delete("/{league_id}/join", response_model=LeagueOut)
def leave(league_id: int, user: User = Depends(profiled_user), db: Session = Depends(get_db)):
    league = load(db, league_id)
    if league.organizer_id == user.id:
        raise HTTPException(400, "Organizers can’t leave their own league")
    row = db.get(LeagueMember, (league.id, user.id))
    if row:
        db.delete(row)
        db.commit()
        db.refresh(league)
    return league_out(league, user.id)
