import re
from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

Sport = Literal["basketball", "soccer", "tennis", "pickleball", "volleyball", "other"]
Skill = Literal["casual", "intermediate", "competitive"]
InvitePolicy = Literal["anyone", "friends", "nobody"]
HANDLE_RE = re.compile(r"^[a-z0-9_]{3,30}$")
TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    password_confirmation: str = Field(min_length=10, max_length=128)
    is_adult: bool
    accepted_agreement: bool

    @field_validator("password_confirmation")
    @classmethod
    def passwords_match_field(cls, value: str, info):
        if info.data.get("password") != value:
            raise ValueError("Passwords do not match")
        return value

    @field_validator("accepted_agreement")
    @classmethod
    def agreement_must_be_accepted(cls, value: bool) -> bool:
        if not value:
            raise ValueError("You must accept the user agreement")
        return value


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class VerifyCodeIn(BaseModel):
    registration_token: str = Field(min_length=32, max_length=128)
    code: str = Field(pattern=r"^\d{6}$")


class ResendCodeIn(BaseModel):
    registration_token: str = Field(min_length=32, max_length=128)


class TokenIn(BaseModel):
    token: str


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str
    password: str = Field(min_length=10, max_length=128)


class SportSkill(BaseModel):
    sport: Sport
    skill: Skill


class ProfileIn(BaseModel):
    handle: str
    display_name: str = Field(min_length=1, max_length=60)
    bio: str | None = Field(None, max_length=160)
    home_area: str | None = Field(None, max_length=80)
    invite_policy: InvitePolicy = "friends"
    sports: list[SportSkill] = Field(default_factory=list)

    @field_validator("handle")
    @classmethod
    def check_handle(cls, v: str) -> str:
        v = v.strip().lower()
        if not HANDLE_RE.match(v):
            raise ValueError("Handle must be 3 to 30 letters, numbers or underscores")
        return v


class Mini(BaseModel):
    handle: str
    display_name: str
    avatar_url: str | None


class ProfileOut(Mini):
    bio: str | None
    home_area: str | None
    invite_policy: InvitePolicy
    sports: list[SportSkill]


class MeOut(BaseModel):
    id: int
    email: str
    email_verified: bool
    profile: ProfileOut | None


class CourtRef(BaseModel):
    id: int
    name: str


class CourtIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    sport: Sport = "basketball"
    address: str | None = Field(None, max_length=200)
    lat: float | None = Field(None, ge=-90, le=90)
    lng: float | None = Field(None, ge=-180, le=180)
    opens: str | None = None
    closes: str | None = None

    @field_validator("opens", "closes")
    @classmethod
    def check_time(cls, v: str | None) -> str | None:
        if v in (None, ""):
            return None
        if not TIME_RE.match(v):
            raise ValueError("Use HH:MM")
        return v


class CourtOut(BaseModel):
    id: int
    name: str
    sport: str
    address: str | None
    lat: float | None
    lng: float | None
    opens: str | None
    closes: str | None
    is_favorite: bool
    distance_mi: float | None


class GameIn(BaseModel):
    court_id: int
    starts_at: datetime
    spots: int = Field(ge=2, le=30)
    min_players: int = Field(ge=2, le=30)
    skill: Skill = "casual"
    note: str | None = Field(None, max_length=200)

    @model_validator(mode="after")
    def validate_player_limits(self):
        if self.min_players > self.spots:
            raise ValueError("Minimum players cannot exceed total spots")
        return self


class GameOut(BaseModel):
    id: int
    court: CourtRef
    host: Mini
    starts_at: datetime
    spots: int
    min_players: int
    skill: str
    note: str | None
    players: int
    joined: bool
    hosted: bool
    status: str
    transfer_expires_at: datetime | None
    cancelled_at: datetime | None


class AttendanceIn(BaseModel):
    attended: list[str]


class LeagueIn(BaseModel):
    court_id: int
    name: str = Field(min_length=2, max_length=80)
    weekday: int = Field(ge=0, le=6)
    time: str
    skill: Skill = "casual"

    @field_validator("time")
    @classmethod
    def check_time(cls, v: str) -> str:
        if not TIME_RE.match(v):
            raise ValueError("Use HH:MM")
        return v


class LeagueOut(BaseModel):
    id: int
    name: str
    court: CourtRef
    weekday: int
    time: str
    skill: str
    organizer: Mini
    members: int
    joined: bool


class Stats(BaseModel):
    games_played: int
    games_hosted: int
    leagues_joined: int
    followers: int
    following: int
    show_up_rate: float | None


class PlaceCount(BaseModel):
    id: int
    name: str
    count: int


class Relationship(BaseModel):
    is_self: bool
    following: bool
    followed_by: bool
    can_invite: bool


class PublicProfile(ProfileOut):
    stats: Stats
    major_courts: list[PlaceCount]
    favorite_courts: list[CourtRef]
    relationship: Relationship


class InviteIn(BaseModel):
    recipient_handle: str
    kind: Literal["game", "league", "note"]
    game_id: int | None = None
    league_id: int | None = None
    note: str | None = Field(None, max_length=200)


class InviteOut(BaseModel):
    id: int
    kind: str
    note: str | None
    status: str
    created_at: datetime
    sender: Mini
    recipient: Mini
    game: GameOut | None
    league: LeagueOut | None