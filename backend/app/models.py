from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

ID = BigInteger().with_variant(Integer, "sqlite")


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def fk(target: str, **kw):
    return mapped_column(ID, ForeignKey(target, ondelete="CASCADE"), **kw)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_adult_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(
        Enum("active", "suspended", "deleted", name="user_status"), default="active"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    profile: Mapped["Profile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )

class PendingRegistration(Base):
    __tablename__ = "pending_registrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    registration_token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_adult_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    accepted_agreement_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    code_hash: Mapped[str] = mapped_column(String(64))
    code_salt: Mapped[str] = mapped_column(String(64))
    code_expires_at: Mapped[datetime] = mapped_column(DateTime)
    resend_available_at: Mapped[datetime] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

class Profile(Base):
    __tablename__ = "profiles"
    user_id: Mapped[int] = fk("users.id", primary_key=True)
    handle: Mapped[str] = mapped_column(String(30), unique=True)
    display_name: Mapped[str] = mapped_column(String(60))
    bio: Mapped[str | None] = mapped_column(String(160), nullable=True)
    home_area: Mapped[str | None] = mapped_column(String(80), nullable=True)
    avatar_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invite_policy: Mapped[str] = mapped_column(
        Enum("anyone", "friends", "nobody", name="invite_policy"), default="friends"
    )
    user: Mapped[User] = relationship(back_populates="profile")
    sports: Mapped[list["UserSport"]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True
    )


class UserSport(Base):
    __tablename__ = "user_sports"
    user_id: Mapped[int] = fk("profiles.user_id", primary_key=True)
    sport: Mapped[str] = mapped_column(String(30), primary_key=True)
    skill: Mapped[str] = mapped_column(Enum("casual", "intermediate", "competitive", name="skill"))


class SessionRow(Base):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = fk("users.id")
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    user: Mapped[User] = relationship()


class EmailToken(Base):
    __tablename__ = "email_tokens"
    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = fk("users.id")
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    purpose: Mapped[str] = mapped_column(Enum("verify", "reset", name="token_purpose"))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Court(Base):
    __tablename__ = "courts"
    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120))
    sport: Mapped[str] = mapped_column(String(30), default="basketball")
    address: Mapped[str | None] = mapped_column(String(200), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    opens: Mapped[str | None] = mapped_column(String(5), nullable=True)
    closes: Mapped[str | None] = mapped_column(String(5), nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        ID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    court_id: Mapped[int] = fk("courts.id")
    host_id: Mapped[int] = fk("users.id")
    starts_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    spots: Mapped[int] = mapped_column(Integer)
    min_players: Mapped[int] = mapped_column(Integer)
    skill: Mapped[str] = mapped_column(String(20), default="casual")
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    transfer_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    court: Mapped[Court] = relationship()
    host: Mapped[User] = relationship()
    rsvps: Mapped[list["Rsvp"]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True
    )

class Rsvp(Base):
    __tablename__ = "rsvps"
    game_id: Mapped[int] = fk("games.id", primary_key=True)
    user_id: Mapped[int] = fk("users.id", primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    attended: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    user: Mapped[User] = relationship()


class League(Base):
    __tablename__ = "leagues"
    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    court_id: Mapped[int] = fk("courts.id")
    organizer_id: Mapped[int] = fk("users.id")
    name: Mapped[str] = mapped_column(String(80))
    weekday: Mapped[int] = mapped_column(Integer)
    time: Mapped[str] = mapped_column(String(5))
    skill: Mapped[str] = mapped_column(String(20), default="casual")
    court: Mapped[Court] = relationship()
    organizer: Mapped[User] = relationship()
    members: Mapped[list["LeagueMember"]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True
    )


class LeagueMember(Base):
    __tablename__ = "league_members"
    league_id: Mapped[int] = fk("leagues.id", primary_key=True)
    user_id: Mapped[int] = fk("users.id", primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Follow(Base):
    __tablename__ = "follows"
    follower_id: Mapped[int] = fk("users.id", primary_key=True)
    followee_id: Mapped[int] = fk("users.id", primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    __table_args__ = (Index("ix_follows_followee", "followee_id"),)


class FavoriteCourt(Base):
    __tablename__ = "user_favorite_courts"
    user_id: Mapped[int] = fk("users.id", primary_key=True)
    court_id: Mapped[int] = fk("courts.id", primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Block(Base):
    __tablename__ = "blocks"
    blocker_id: Mapped[int] = fk("users.id", primary_key=True)
    blocked_id: Mapped[int] = fk("users.id", primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Invite(Base):
    __tablename__ = "invites"
    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    sender_id: Mapped[int] = fk("users.id")
    recipient_id: Mapped[int] = fk("users.id")
    kind: Mapped[str] = mapped_column(Enum("game", "league", "note", name="invite_kind"))
    game_id: Mapped[int | None] = mapped_column(
        ID, ForeignKey("games.id", ondelete="CASCADE"), nullable=True
    )
    league_id: Mapped[int | None] = mapped_column(
        ID, ForeignKey("leagues.id", ondelete="CASCADE"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("pending", "accepted", "declined", "expired", name="invite_status"), default="pending"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    game: Mapped[Game | None] = relationship()
    league: Mapped[League | None] = relationship()
    sender: Mapped[User] = relationship(foreign_keys=[sender_id])
    recipient: Mapped[User] = relationship(foreign_keys=[recipient_id])
    __table_args__ = (
        Index("ix_invites_recipient", "recipient_id", "status"),
        CheckConstraint(
            "(kind='game' AND game_id IS NOT NULL) OR (kind='league' AND league_id IS NOT NULL) OR kind='note'",
            name="ck_invite_target",
        ),
    )
