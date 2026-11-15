
import io
import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile
from PIL import Image, ImageOps
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..deps import COOKIE, get_user, profiled_user, verified_user
from ..models import (
    Court,
    FavoriteCourt,
    Game,
    Profile,
    Rsvp,
    User,
    UserSport,
    utcnow,
)
from ..schemas import GameOut, MeOut, ProfileIn, ProfileOut
from ..services import game_out, profile_out

router = APIRouter(prefix="/me", tags=["me"])


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


@router.get("", response_model=MeOut)
def me(user: User = Depends(get_user)):
    return {
        "id": user.id,
        "email": user.email,
        "email_verified": user.email_verified_at is not None,
        "profile": profile_out(user),
    }


@router.put("/profile", response_model=ProfileOut)
def save_profile(
    body: ProfileIn,
    user: User = Depends(verified_user),
    db: Session = Depends(get_db),
):
    profile = user.profile

    if not profile:
        profile = Profile(
            user_id=user.id,
            handle=body.handle,
            display_name=body.display_name,
        )
        db.add(profile)

    profile.handle = body.handle
    profile.display_name = body.display_name.strip()
    profile.bio = body.bio
    profile.home_area = body.home_area
    profile.invite_policy = body.invite_policy

    db.execute(delete(UserSport).where(UserSport.user_id == user.id))
    db.flush()

    seen = set()

    for sport in body.sports:
        if sport.sport not in seen:
            seen.add(sport.sport)
            db.add(
                UserSport(
                    user_id=user.id,
                    sport=sport.sport,
                    skill=sport.skill,
                )
            )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "That handle is taken")

    db.refresh(user)
    return profile_out(user)


@router.post("/avatar", response_model=ProfileOut)
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(profiled_user),
    db: Session = Depends(get_db),
):
    if not user.profile:
        raise HTTPException(409, "Complete your profile before uploading an avatar")

    data = await file.read(5 * 1024 * 1024 + 1)

    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, "Image must be under 5 MB")

    try:
        image = Image.open(io.BytesIO(data))

        if image.format not in {"JPEG", "PNG", "WEBP"}:
            raise ValueError

        image = ImageOps.exif_transpose(image).convert("RGB")

    except Exception:
        raise HTTPException(400, "Upload a JPEG, PNG or WebP image")

    image = ImageOps.fit(image, (256, 256))

    folder = Path(settings.upload_dir) / "avatars"
    folder.mkdir(parents=True, exist_ok=True)

    key = f"{secrets.token_hex(8)}.webp"
    image.save(folder / key, "WEBP", quality=85)

    old = user.profile.avatar_key
    user.profile.avatar_key = key

    db.commit()

    if old:
        (folder / old).unlink(missing_ok=True)

    return profile_out(user)


@router.put("/favorites/{court_id}")
def add_favorite(
    court_id: int,
    user: User = Depends(get_user),
    db: Session = Depends(get_db),
):
    if not db.get(Court, court_id):
        raise HTTPException(404, "Court not found")

    if not db.get(FavoriteCourt, (user.id, court_id)):
        db.add(FavoriteCourt(user_id=user.id, court_id=court_id))
        db.commit()

    return {"ok": True}


@router.delete("/favorites/{court_id}")
def remove_favorite(
    court_id: int,
    user: User = Depends(get_user),
    db: Session = Depends(get_db),
):
    db.execute(
        delete(FavoriteCourt).where(
            FavoriteCourt.user_id == user.id,
            FavoriteCourt.court_id == court_id,
        )
    )
    db.commit()

    return {"ok": True}


@router.get("/games", response_model=list[GameOut])
def my_games(
    user: User = Depends(get_user),
    db: Session = Depends(get_db),
):
    user_rsvps = select(Rsvp.game_id).where(Rsvp.user_id == user.id)

    games = db.scalars(
        select(Game)
        .where(
            (Game.id.in_(user_rsvps)) |
            (Game.host_id == user.id)
        )
        .order_by(Game.starts_at.desc())
        .limit(100)
    ).all()

    changed = False

    for game in games:
        if expire_transfer(game):
            changed = True

    if changed:
        db.commit()

    return [game_out(game, user.id) for game in games]


@router.delete("")
def delete_account(
    request: Request,
    response: Response,
    user: User = Depends(get_user),
    db: Session = Depends(get_db),
):
    old = user.profile.avatar_key if user.profile else None

    db.delete(user)
    db.commit()

    if old:
        (Path(settings.upload_dir) / "avatars" / old).unlink(
            missing_ok=True
        )

    response.delete_cookie(COOKIE, path="/")

    return {"ok": True}
