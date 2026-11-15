
import math
from datetime import timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import models as m
from .models import utcnow


def avatar_url(profile: m.Profile | None) -> str | None:
    return f"/uploads/avatars/{profile.avatar_key}" if profile and profile.avatar_key else None


def mini(user: m.User) -> dict:
    p = user.profile
    return {
        "handle": p.handle if p else "unknown",
        "display_name": p.display_name if p else "Unknown",
        "avatar_url": avatar_url(p),
    }


def profile_out(user: m.User) -> dict | None:
    p = user.profile
    if not p:
        return None

    return {
        **mini(user),
        "bio": p.bio,
        "home_area": p.home_area,
        "invite_policy": p.invite_policy,
        "sports": [{"sport": s.sport, "skill": s.skill} for s in p.sports],
    }


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = lambda x: math.radians(x)
    a = (
        math.sin(r(lat2 - lat1) / 2) ** 2
        + math.cos(r(lat1))
        * math.cos(r(lat2))
        * math.sin(r(lng2 - lng1) / 2) ** 2
    )
    return 3958.8 * 2 * math.asin(math.sqrt(a))


def favorite_ids(db: Session, user_id: int) -> set[int]:
    return set(
        db.scalars(
            select(m.FavoriteCourt.court_id).where(
                m.FavoriteCourt.user_id == user_id
            )
        )
    )


def court_out(
    court: m.Court,
    favs: set[int],
    lat: float | None = None,
    lng: float | None = None,
) -> dict:
    dist = None

    if (
        lat is not None
        and lng is not None
        and court.lat is not None
        and court.lng is not None
    ):
        dist = round(haversine(lat, lng, court.lat, court.lng), 2)

    return {
        "id": court.id,
        "name": court.name,
        "sport": court.sport,
        "address": court.address,
        "lat": court.lat,
        "lng": court.lng,
        "opens": court.opens,
        "closes": court.closes,
        "is_favorite": court.id in favs,
        "distance_mi": dist,
    }


def game_out(game: m.Game, viewer_id: int) -> dict:
    return {
        "id": game.id,
        "court": {"id": game.court.id, "name": game.court.name},
        "host": mini(game.host),
        "starts_at": game.starts_at.replace(tzinfo=timezone.utc),
        "spots": game.spots,
        "min_players": game.min_players,
        "skill": game.skill,
        "note": game.note,
        "players": len(game.rsvps),
        "joined": any(r.user_id == viewer_id for r in game.rsvps),
        "hosted": game.host_id == viewer_id,
        "status": game.status,
        "transfer_expires_at": (
            game.transfer_expires_at.replace(tzinfo=timezone.utc)
            if game.transfer_expires_at
            else None
        ),
        "cancelled_at": (
            game.cancelled_at.replace(tzinfo=timezone.utc)
            if game.cancelled_at
            else None
        ),
    }


def league_out(league: m.League, viewer_id: int) -> dict:
    return {
        "id": league.id,
        "name": league.name,
        "court": {"id": league.court.id, "name": league.court.name},
        "weekday": league.weekday,
        "time": league.time,
        "skill": league.skill,
        "organizer": mini(league.organizer),
        "members": len(league.members),
        "joined": any(x.user_id == viewer_id for x in league.members),
    }


def is_blocked(db: Session, a: int, b: int) -> bool:
    return (
        db.scalar(
            select(func.count())
            .select_from(m.Block)
            .where(
                ((m.Block.blocker_id == a) & (m.Block.blocked_id == b))
                | ((m.Block.blocker_id == b) & (m.Block.blocked_id == a))
            )
        )
        > 0
    )


def follows(db: Session, a: int, b: int) -> bool:
    return db.get(m.Follow, (a, b)) is not None


def can_invite(db: Session, sender: m.User, target: m.User) -> bool:
    if (
        sender.id == target.id
        or not target.profile
        or is_blocked(db, sender.id, target.id)
    ):
        return False

    policy = target.profile.invite_policy

    if policy == "anyone":
        return True

    if policy == "friends":
        return follows(db, sender.id, target.id) and follows(
            db, target.id, sender.id
        )

    return False


def stats(db: Session, uid: int) -> dict:
    now = utcnow()

    count = lambda q: db.scalar(q) or 0

    played = count(
        select(func.count())
        .select_from(m.Rsvp)
        .join(m.Game, m.Game.id == m.Rsvp.game_id)
        .where(
            m.Rsvp.user_id == uid,
            m.Game.starts_at < now,
            m.Game.status != "cancelled",
        )
    )

    hosted = count(
        select(func.count())
        .select_from(m.Game)
        .where(
            m.Game.host_id == uid,
            m.Game.status != "cancelled",
        )
    )

    leagues = count(
        select(func.count())
        .select_from(m.LeagueMember)
        .where(m.LeagueMember.user_id == uid)
    )

    followers = count(
        select(func.count())
        .select_from(m.Follow)
        .where(m.Follow.followee_id == uid)
    )

    following = count(
        select(func.count())
        .select_from(m.Follow)
        .where(m.Follow.follower_id == uid)
    )

    rated = count(
        select(func.count())
        .select_from(m.Rsvp)
        .where(
            m.Rsvp.user_id == uid,
            m.Rsvp.attended.is_not(None),
        )
    )

    came = count(
        select(func.count())
        .select_from(m.Rsvp)
        .where(
            m.Rsvp.user_id == uid,
            m.Rsvp.attended.is_(True),
        )
    )

    return {
        "games_played": played,
        "games_hosted": hosted,
        "leagues_joined": leagues,
        "followers": followers,
        "following": following,
        "show_up_rate": round(came / rated, 2) if rated else None,
    }


def major_courts(db: Session, uid: int) -> list[dict]:
    now = utcnow()

    rows = db.execute(
        select(m.Court.id, m.Court.name, func.count().label("n"))
        .select_from(m.Rsvp)
        .join(m.Game, m.Game.id == m.Rsvp.game_id)
        .join(m.Court, m.Court.id == m.Game.court_id)
        .where(
            m.Rsvp.user_id == uid,
            m.Game.starts_at < now,
            m.Game.starts_at > now - timedelta(days=90),
            m.Game.status != "cancelled",
        )
        .group_by(m.Court.id, m.Court.name)
        .order_by(func.count().desc())
        .limit(3)
    ).all()

    return [
        {"id": r[0], "name": r[1], "count": r[2]}
        for r in rows
    ]


def public_profile(db: Session, target: m.User, viewer: m.User) -> dict:
    favs = db.execute(
        select(m.Court.id, m.Court.name)
        .join(m.FavoriteCourt, m.FavoriteCourt.court_id == m.Court.id)
        .where(m.FavoriteCourt.user_id == target.id)
    ).all()

    return {
        **profile_out(target),
        "stats": stats(db, target.id),
        "major_courts": major_courts(db, target.id),
        "favorite_courts": [
            {"id": r[0], "name": r[1]}
            for r in favs
        ],
        "relationship": {
            "is_self": viewer.id == target.id,
            "following": follows(db, viewer.id, target.id),
            "followed_by": follows(db, target.id, viewer.id),
            "can_invite": can_invite(db, viewer, target),
        },
    }
