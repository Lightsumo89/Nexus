
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import profiled_user
from ..models import Block, Follow, Profile, User, UserSport
from ..schemas import Mini, PublicProfile
from ..services import is_blocked, mini, public_profile


router = APIRouter(prefix="/users", tags=["users"])


def target_of(db: Session, handle: str, viewer: User) -> User:
    profile = db.scalar(
        select(Profile).where(Profile.handle == handle.lower())
    )

    if not profile or profile.user.status != "active":
        raise HTTPException(404, "Profile not found")

    if profile.user_id != viewer.id and is_blocked(
        db, viewer.id, profile.user_id
    ):
        raise HTTPException(404, "Profile not found")

    return profile.user


@router.get("/search", response_model=list[Mini])
def search_users(
    q: str = Query(min_length=2, max_length=60),
    sport: str | None = None,
    viewer: User = Depends(profiled_user),
    db: Session = Depends(get_db),
):
    term = q.strip().lower()

    if len(term) < 2:
        return []

    stmt = (
        select(Profile)
        .join(User, Profile.user_id == User.id)
        .where(
            User.status == "active",
            Profile.user_id != viewer.id,
            (
                func.lower(Profile.handle).contains(term)
                | func.lower(Profile.display_name).contains(term)
            ),
        )
        .order_by(func.lower(Profile.handle))
        .limit(100)
    )

    if sport:
        stmt = stmt.where(
            Profile.sports.any(
                UserSport.sport == sport.strip().lower()
            )
        )

    profiles = db.scalars(stmt).all()

    results = [
        mini(profile.user)
        for profile in profiles
        if not is_blocked(db, viewer.id, profile.user_id)
    ]

    return results[:30]


@router.get("/{handle}", response_model=PublicProfile)
def get_profile(
    handle: str,
    viewer: User = Depends(profiled_user),
    db: Session = Depends(get_db),
):
    return public_profile(db, target_of(db, handle, viewer), viewer)


@router.post("/{handle}/follow")
def follow(
    handle: str,
    viewer: User = Depends(profiled_user),
    db: Session = Depends(get_db),
):
    target = target_of(db, handle, viewer)

    if target.id == viewer.id:
        raise HTTPException(400, "You can’t follow yourself")

    if not db.get(Follow, (viewer.id, target.id)):
        db.add(Follow(follower_id=viewer.id, followee_id=target.id))
        db.commit()

    return {"ok": True}


@router.delete("/{handle}/follow")
def unfollow(
    handle: str,
    viewer: User = Depends(profiled_user),
    db: Session = Depends(get_db),
):
    target = target_of(db, handle, viewer)

    db.execute(
        delete(Follow).where(
            Follow.follower_id == viewer.id,
            Follow.followee_id == target.id,
        )
    )
    db.commit()

    return {"ok": True}


@router.post("/{handle}/block")
def block(
    handle: str,
    viewer: User = Depends(profiled_user),
    db: Session = Depends(get_db),
):
    target = target_of(db, handle, viewer)

    if target.id == viewer.id:
        raise HTTPException(400, "You can’t block yourself")

    if not db.get(Block, (viewer.id, target.id)):
        db.add(Block(blocker_id=viewer.id, blocked_id=target.id))

    db.execute(
        delete(Follow).where(
            (
                (Follow.follower_id == viewer.id)
                & (Follow.followee_id == target.id)
            )
            | (
                (Follow.follower_id == target.id)
                & (Follow.followee_id == viewer.id)
            )
        )
    )

    db.commit()

    return {"ok": True}

