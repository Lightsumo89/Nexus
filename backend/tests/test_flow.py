import os
import tempfile

tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/test.db"
os.environ["UPLOAD_DIR"] = f"{tmp}/uploads"

from datetime import datetime, timedelta, timezone  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

PASSWORD = "a-long-enough-password"


def future(hours=3):
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def signup_payload(email, **overrides):
    payload = {
        "email": email,
        "password": PASSWORD,
        "password_confirmation": PASSWORD,
        "is_adult": True,
        "accepted_agreement": True,
    }
    payload.update(overrides)
    return payload


def make_user(email, handle, name):
    c = TestClient(app)

    response = c.post(
        "/api/auth/signup",
        json=signup_payload(email),
    )
    assert response.status_code == 201, response.text

    data = response.json()
    assert "registration_token" in data
    assert "dev_code" in data, data

    verification = c.post(
        "/api/auth/verify",
        json={
            "registration_token": data["registration_token"],
            "code": data["dev_code"],
        },
    )
    assert verification.status_code == 200, verification.text

    response = c.put(
        "/api/me/profile",
        json={
            "handle": handle,
            "display_name": name,
            "invite_policy": "anyone",
            "sports": [{"sport": "basketball", "skill": "casual"}],
        },
    )
    assert response.status_code == 200, response.text

    return c


def test_signup_gates():
    c = TestClient(app)

    assert c.get("/api/me").status_code == 401

    # Reject weak passwords.
    assert c.post(
        "/api/auth/signup",
        json=signup_payload(
            "weak@example.com",
            password="short",
            password_confirmation="short",
        ),
    ).status_code == 422

    # Reject mismatched passwords.
    assert c.post(
        "/api/auth/signup",
        json=signup_payload(
            "mismatch@example.com",
            password_confirmation="different-password",
        ),
    ).status_code == 422

    # Require adult confirmation.
    assert c.post(
        "/api/auth/signup",
        json=signup_payload(
            "underage@example.com",
            is_adult=False,
        ),
    ).status_code == 422

    # Require agreement acceptance.
    assert c.post(
        "/api/auth/signup",
        json=signup_payload(
            "agreement@example.com",
            accepted_agreement=False,
        ),
    ).status_code == 422

    # A valid signup creates a pending registration, not a session.
    response = c.post(
        "/api/auth/signup",
        json=signup_payload("x@example.com"),
    )
    assert response.status_code == 201, response.text

    data = response.json()
    assert "registration_token" in data
    assert "dev_code" in data
    assert c.get("/api/me").status_code == 401

    # A second pending registration for the same email is rejected.
    duplicate = c.post(
        "/api/auth/signup",
        json=signup_payload("X@example.com"),
    )
    assert duplicate.status_code == 409, duplicate.text

    # An incorrect code must not create a session.
    wrong_code = (
        "000001" if data["dev_code"] == "000000" else "000000"
    )
    response = c.post(
        "/api/auth/verify",
        json={
            "registration_token": data["registration_token"],
            "code": wrong_code,
        },
    )
    assert response.status_code == 400, response.text
    assert c.get("/api/me").status_code == 401

    # The correct code verifies the email and starts a session.
    response = c.post(
        "/api/auth/verify",
        json={
            "registration_token": data["registration_token"],
            "code": data["dev_code"],
        },
    )
    assert response.status_code == 200, response.text
    assert c.get("/api/me").json()["email_verified"] is True


def test_login_logout():
    c = make_user("login@example.com", "login_user", "Login")

    c.post("/api/auth/logout")
    assert c.get("/api/me").status_code == 401

    assert c.post(
        "/api/auth/login",
        json={
            "email": "login@example.com",
            "password": "wrong-password-here",
        },
    ).status_code == 401

    response = c.post(
        "/api/auth/login",
        json={
            "email": "LOGIN@example.com",
            "password": PASSWORD,
        },
    )
    assert response.status_code == 200, response.text
    assert c.get("/api/me").json()["profile"]["handle"] == "login_user"


def test_full_flow():
    a = make_user("a@example.com", "alice", "Alice")
    b = make_user("b@example.com", "bob", "Bob")

    court_response = a.post(
        "/api/courts",
        json={
            "name": "Test Court",
            "sport": "basketball",
            "lat": 42.39,
            "lng": -71.1,
            "closes": "22:00",
        },
    )
    assert court_response.status_code in (200, 201), court_response.text
    court = court_response.json()

    assert a.post(
        "/api/courts",
        json={"name": "Bad", "opens": "25:99"},
    ).status_code == 422

    game_response = a.post(
        "/api/games",
        json={
            "court_id": court["id"],
            "starts_at": future(),
            "spots": 2,
            "min_players": 2,
        },
    )
    assert game_response.status_code in (200, 201), game_response.text
    game = game_response.json()

    assert game["players"] == 1 and game["hosted"] is True

    assert a.post(
        "/api/games",
        json={
            "court_id": court["id"],
            "starts_at": future(-5),
            "spots": 4,
            "min_players": 2,
        },
    ).status_code == 422

    assert len(b.get("/api/games").json()) == 1

    joined = b.post(f"/api/games/{game['id']}/join").json()
    assert joined["players"] == 2 and joined["joined"] is True

    c = make_user("c@example.com", "carol", "Carol")
    assert c.post(f"/api/games/{game['id']}/join").status_code == 409

    assert b.delete(f"/api/games/{game['id']}/join").json()["players"] == 1
    assert a.delete(f"/api/games/{game['id']}/join").status_code == 400

    assert b.post("/api/users/alice/follow").status_code == 200
    assert b.post("/api/users/bob/follow").status_code == 400

    profile = b.get("/api/users/alice").json()
    assert profile["relationship"]["following"] is True
    assert profile["stats"]["followers"] == 1
    assert profile["stats"]["games_hosted"] == 1

    assert b.put(f"/api/me/favorites/{court['id']}").status_code == 200
    assert b.get("/api/users/bob").json()["favorite_courts"][0]["name"] == "Test Court"

    invite = a.post(
        "/api/invites",
        json={
            "recipient_handle": "bob",
            "kind": "game",
            "game_id": game["id"],
            "note": "come run",
        },
    )
    assert invite.status_code == 201, invite.text

    assert a.post(
        "/api/invites",
        json={
            "recipient_handle": "bob",
            "kind": "game",
            "game_id": game["id"],
        },
    ).status_code == 409

    assert b.post(
        "/api/invites",
        json={
            "recipient_handle": "alice",
            "kind": "game",
            "game_id": game["id"],
        },
    ).status_code == 403

    assert a.post(
        "/api/invites",
        json={"recipient_handle": "bob", "kind": "note"},
    ).status_code == 422

    inbox = b.get("/api/invites").json()["received"]
    assert len(inbox) == 1
    assert inbox[0]["game"]["id"] == game["id"]

    assert b.post(f"/api/invites/{inbox[0]['id']}/accept").status_code == 200
    assert b.post(f"/api/invites/{inbox[0]['id']}/accept").status_code == 409
    assert b.get("/api/games").json()[0]["joined"] is True

    league_response = a.post(
        "/api/leagues",
        json={
            "court_id": court["id"],
            "name": "Wed Run",
            "weekday": 3,
            "time": "19:00",
        },
    )
    assert league_response.status_code in (200, 201), league_response.text
    league = league_response.json()

    assert league["members"] == 1
    assert b.post(f"/api/leagues/{league['id']}/join").json()["members"] == 2
    assert len(a.get("/api/leagues?organizing=true").json()) == 1


def test_block_hides_profile():
    a = make_user("blk-a@example.com", "blocker", "Blocker")
    b = make_user("blk-b@example.com", "blocked", "Blocked")

    assert a.post("/api/users/blocked/block").status_code == 200
    assert b.get("/api/users/blocker").status_code == 404

    assert b.post(
        "/api/invites",
        json={
            "recipient_handle": "blocker",
            "kind": "note",
            "note": "hi",
        },
    ).status_code == 403


def test_attendance_and_delete():
    a = make_user("att-a@example.com", "host_a", "Host")

    court_response = a.post(
        "/api/courts",
        json={"name": "Att Court"},
    )
    assert court_response.status_code in (200, 201), court_response.text
    court = court_response.json()

    game_response = a.post(
        "/api/games",
        json={
            "court_id": court["id"],
            "starts_at": future(1),
            "spots": 4,
            "min_players": 2,
        },
    )
    assert game_response.status_code in (200, 201), game_response.text
    game = game_response.json()

    assert a.post(
        f"/api/games/{game['id']}/attendance",
        json={"attended": ["host_a"]},
    ).status_code == 409

    assert a.delete("/api/me").status_code == 200
    assert a.get("/api/me").status_code == 401