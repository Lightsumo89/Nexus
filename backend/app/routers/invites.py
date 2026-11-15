
from datetime import timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import profiled_user
from ..models import Game, Invite, League, LeagueMember, Profile, Rsvp, User, utcnow
from ..schemas import InviteIn, InviteOut
from ..services import can_invite, game_out, league_out, mini

router = APIRouter(prefix="/invites", tags=["invites"])
DAILY_LIMIT = 20


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


def invite_out(inv: Invite, viewer_id: int) -> dict:
    return {
        "id": inv.id,
        "kind": inv.kind,
        "note": inv.note,
        "status": inv.status,
        "created_at": inv.created_at.replace(tzinfo=timezone.utc),
        "sender": mini(inv.sender),
        "recipient": mini(inv.recipient),
        "game": game_out(inv.game, viewer_id) if inv.game else None,
        "league": league_out(inv.league, viewer_id) if inv.league else None,
    }


@router.post("", response_model=InviteOut, status_code=201)
def send(
    body: InviteIn,
    user: User = Depends(profiled_user),
    db: Session = Depends(get_db),
):
    profile = db.scalar(
        select(Profile).where(Profile.handle == body.recipient_handle.lower())
    )

    if not profile or not can_invite(db, user, profile.user):
        raise HTTPException(403, "You can't invite this person")

    since = utcnow() - timedelta(days=1)

    sent_today = db.scalar(
        select(func.count())
        .select_from(Invite)
        .where(
            Invite.sender_id == user.id,
            Invite.created_at > since,
        )
    )

    if sent_today >= DAILY_LIMIT:
        raise HTTPException(429, "Daily invite limit reached")

    target = profile.user
    game_id = None
    league_id = None
    note = (body.note or "").strip() or None

    if body.kind == "game":
        game = (
            db.scalar(
                select(Game)
                .where(Game.id == body.game_id)
                .with_for_update()
            )
            if body.game_id
            else None
        )

        if not game or game.host_id != user.id:
            raise HTTPException(403, "You can only invite to games you host")

        if expire_transfer(game):
            db.commit()
            raise HTTPException(409, "This game has been cancelled")

        if game.status != "active":
            raise HTTPException(409, "This game is not accepting invitations")

        if game.starts_at < utcnow():
            raise HTTPException(409, "That game has already started")

        if any(r.user_id == target.id for r in game.rsvps):
            raise HTTPException(409, "They're already in this game")

        game_id = game.id

    elif body.kind == "league":
        league = db.get(League, body.league_id) if body.league_id else None

        if not league or league.organizer_id != user.id:
            raise HTTPException(403, "You can only invite to leagues you organize")

        if db.get(LeagueMember, (league.id, target.id)):
            raise HTTPException(409, "They're already in this league")

        league_id = league.id

    elif not note:
        raise HTTPException(422, "Write a short note")

    same = [
        Invite.sender_id == user.id,
        Invite.recipient_id == target.id,
        Invite.status == "pending",
        Invite.kind == body.kind,
    ]

    same.append(
        Invite.game_id == game_id
        if game_id
        else Invite.game_id.is_(None)
    )

    same.append(
        Invite.league_id == league_id
        if league_id
        else Invite.league_id.is_(None)
    )

    if note and body.kind == "note":
        same.append(Invite.note == note)

    if db.scalar(select(func.count()).select_from(Invite).where(*same)):
        raise HTTPException(409, "You already sent this invite")

    inv = Invite(
        sender_id=user.id,
        recipient_id=target.id,
        kind=body.kind,
        game_id=game_id,
        league_id=league_id,
        note=note,
    )

    db.add(inv)
    db.commit()
    db.refresh(inv)

    return invite_out(inv, user.id)


@router.get("")
def mine(
    user: User = Depends(profiled_user),
    db: Session = Depends(get_db),
):
    since = utcnow() - timedelta(days=30)

    received = db.scalars(
        select(Invite)
        .where(
            Invite.recipient_id == user.id,
            Invite.created_at > since,
        )
        .order_by(Invite.created_at.desc())
        .limit(50)
    ).all()

    sent = db.scalars(
        select(Invite)
        .where(
            Invite.sender_id == user.id,
            Invite.created_at > since,
        )
        .order_by(Invite.created_at.desc())
        .limit(50)
    ).all()

    return {
        "received": [invite_out(inv, user.id) for inv in received],
        "sent": [invite_out(inv, user.id) for inv in sent],
    }


def respond(db: Session, invite_id: int, user: User) -> Invite:
    inv = db.scalar(
        select(Invite)
        .where(Invite.id == invite_id)
        .with_for_update()
    )

    if not inv or inv.recipient_id != user.id:
        raise HTTPException(404, "Invite not found")

    if inv.status != "pending":
        raise HTTPException(409, "You already responded to this invite")

    return inv


@router.post("/{invite_id}/accept")
def accept(
    invite_id: int,
    user: User = Depends(profiled_user),
    db: Session = Depends(get_db),
):
    inv = respond(db, invite_id, user)

    if inv.kind == "game" and inv.game:
        game = db.scalar(
            select(Game)
            .where(Game.id == inv.game.id)
            .with_for_update()
        )

        if not game:
            raise HTTPException(404, "Game not found")

        if expire_transfer(game):
            db.commit()
            raise HTTPException(409, "This game has been cancelled")

        if game.status != "active":
            raise HTTPException(409, "This game is not accepting participants")

        if game.starts_at < utcnow():
            raise HTTPException(409, "This game has already started")

        if not db.get(Rsvp, (game.id, user.id)):
            if len(game.rsvps) >= game.spots:
                raise HTTPException(409, "This game is full")

            db.add(Rsvp(game_id=game.id, user_id=user.id))

    elif inv.kind == "league" and inv.league:
        if not db.get(LeagueMember, (inv.league.id, user.id)):
            db.add(
                LeagueMember(
                    league_id=inv.league.id,
                    user_id=user.id,
                )
            )

    inv.status = "accepted"
    inv.responded_at = utcnow()

    db.commit()

    return {"ok": True}


@router.post("/{invite_id}/decline")
def decline(
    invite_id: int,
    user: User = Depends(profiled_user),
    db: Session = Depends(get_db),
):
    inv = respond(db, invite_id, user)

    inv.status = "declined"
    inv.responded_at = utcnow()

    db.commit()

    return {"ok": True}
