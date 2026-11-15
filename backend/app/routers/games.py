from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import profiled_user
from ..models import Court, Game, Rsvp, User, utcnow
from ..schemas import AttendanceIn, GameIn, GameOut
from ..services import game_out, is_blocked

router = APIRouter(prefix="/games", tags=["games"])

TRANSFER_WINDOW = timedelta(minutes=2)


def naive_utc(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc).replace(tzinfo=None) if dt.tzinfo else dt


def expire_transfer(game: Game) -> bool:
    if (
        game.status == "host_transfer_pending"
        and game.transfer_expires_at is not None
        and game.transfer_expires_at <= utcnow()
    ):
        game.status = "cancelled"
        game.cancelled_at = utcnow()
        game.transfer_expires_at = None
        return True

    return False


def load(db: Session, game_id: int, lock: bool = False) -> Game:
    stmt = select(Game).where(Game.id == game_id)

    if lock:
        stmt = stmt.with_for_update()

    game = db.scalar(stmt)

    if not game:
        raise HTTPException(404, "Game not found")

    if expire_transfer(game):
        db.commit()
        db.refresh(game)

        if lock:
            game = db.scalar(stmt)

    return game


def require_active(game: Game):
    if game.status == "cancelled":
        raise HTTPException(409, "This game has been cancelled")

    if game.status == "host_transfer_pending":
        raise HTTPException(409, "This game is awaiting a new host")


@router.get("", response_model=list[GameOut])
def list_games(
    court_id: int | None = None,
    days: int = 7,
    user: User = Depends(profiled_user),
    db: Session = Depends(get_db),
):
    now = utcnow()

    stmt = select(Game).where(
        Game.starts_at >= now - timedelta(hours=2),
        Game.starts_at <= now + timedelta(days=min(days, 30)),
        Game.status != "cancelled",
    )

    if court_id:
        stmt = stmt.where(Game.court_id == court_id)

    games = db.scalars(stmt.order_by(Game.starts_at).limit(200)).all()

    changed = False

    for game in games:
        if expire_transfer(game):
            changed = True

    if changed:
        db.commit()

    return [
        game_out(game, user.id)
        for game in games
        if game.status == "active"
        and not is_blocked(db, user.id, game.host_id)
    ]


@router.post("", response_model=GameOut, status_code=201)
def create_game(
    body: GameIn,
    user: User = Depends(profiled_user),
    db: Session = Depends(get_db),
):
    starts = naive_utc(body.starts_at)

    if starts < utcnow():
        raise HTTPException(422, "Start time is in the past")

    if not db.get(Court, body.court_id):
        raise HTTPException(404, "Court not found")

    game = Game(
        court_id=body.court_id,
        host_id=user.id,
        starts_at=starts,
        spots=body.spots,
        min_players=body.min_players,
        skill=body.skill,
        note=body.note,
        status="active",
    )

    db.add(game)
    db.flush()

    db.add(Rsvp(game_id=game.id, user_id=user.id))

    db.commit()
    db.refresh(game)

    return game_out(game, user.id)


@router.post("/{game_id}/join", response_model=GameOut)
def join(
    game_id: int,
    user: User = Depends(profiled_user),
    db: Session = Depends(get_db),
):
    game = load(db, game_id, lock=True)
    require_active(game)

    if is_blocked(db, user.id, game.host_id):
        raise HTTPException(403, "You can't join this game")

    if game.starts_at < utcnow() - timedelta(hours=2):
        raise HTTPException(409, "This game has already happened")

    existing = db.get(Rsvp, (game.id, user.id))

    if not existing:
        if len(game.rsvps) >= game.spots:
            raise HTTPException(409, "This game is full")

        db.add(Rsvp(game_id=game.id, user_id=user.id))
        db.commit()
        db.refresh(game)

    return game_out(game, user.id)


@router.delete("/{game_id}/join", response_model=GameOut)
def leave(
    game_id: int,
    user: User = Depends(profiled_user),
    db: Session = Depends(get_db),
):
    game = load(db, game_id, lock=True)
    require_active(game)

    row = db.get(Rsvp, (game.id, user.id))

    if row:
        db.delete(row)
        db.commit()
        db.refresh(game)

    return game_out(game, user.id)


@router.post("/{game_id}/transfer", response_model=GameOut)
def start_host_transfer(
    game_id: int,
    user: User = Depends(profiled_user),
    db: Session = Depends(get_db),
):
    game = load(db, game_id, lock=True)
    require_active(game)

    if game.host_id != user.id:
        raise HTTPException(403, "Only the host can transfer ownership")

    if game.starts_at < utcnow():
        raise HTTPException(409, "You can't transfer a game that has already started")

    now = utcnow()

    game.status = "host_transfer_pending"
    game.transfer_expires_at = now + TRANSFER_WINDOW

    host_rsvp = db.get(Rsvp, (game.id, user.id))

    if host_rsvp:
        db.delete(host_rsvp)

    db.commit()
    db.refresh(game)

    return game_out(game, user.id)


@router.post("/{game_id}/claim", response_model=GameOut)
def claim_host(
    game_id: int,
    user: User = Depends(profiled_user),
    db: Session = Depends(get_db),
):
    game = load(db, game_id, lock=True)

    if game.status == "cancelled":
        raise HTTPException(409, "This game has been cancelled")

    if game.status != "host_transfer_pending":
        raise HTTPException(409, "This game is not awaiting a new host")

    if game.starts_at < utcnow():
        raise HTTPException(409, "This game has already started")

    if game.host_id == user.id:
        raise HTTPException(409, "You are already the host")

    if is_blocked(db, user.id, game.host_id):
        raise HTTPException(403, "You can't claim this game")

    participant_rsvp = db.get(Rsvp, (game.id, user.id))

    if not participant_rsvp:
        raise HTTPException(403, "Only current participants can claim ownership")

    db.delete(participant_rsvp)

    game.host_id = user.id
    game.status = "active"
    game.transfer_expires_at = None

    db.commit()
    db.refresh(game)

    return game_out(game, user.id)


@router.delete("/{game_id}", response_model=GameOut)
def cancel_game(
    game_id: int,
    user: User = Depends(profiled_user),
    db: Session = Depends(get_db),
):
    game = load(db, game_id, lock=True)

    if game.host_id != user.id:
        raise HTTPException(403, "Only the host can cancel this game")

    if game.status == "cancelled":
        return game_out(game, user.id)

    game.status = "cancelled"
    game.cancelled_at = utcnow()
    game.transfer_expires_at = None

    db.commit()
    db.refresh(game)

    return game_out(game, user.id)


@router.post("/{game_id}/attendance")
def attendance(
    game_id: int,
    body: AttendanceIn,
    user: User = Depends(profiled_user),
    db: Session = Depends(get_db),
):
    game = load(db, game_id)
    require_active(game)

    if game.host_id != user.id:
        raise HTTPException(403, "Only the host can record attendance")

    if game.starts_at > utcnow():
        raise HTTPException(409, "The game hasn't started yet")

    came = {handle.lower() for handle in body.attended}

    for rsvp in game.rsvps:
        rsvp.attended = (
            rsvp.user.profile.handle in came
            if rsvp.user.profile
            else False
        )

    db.commit()

    return {"ok": True}