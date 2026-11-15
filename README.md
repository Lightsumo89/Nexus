# Pickup draft

A local draft of the pickup-games app: React + TypeScript frontend, FastAPI backend, MySQL.

## What works

Accounts with email and password (Argon2 hashes, server-side sessions in an httpOnly cookie), email verification, password reset, an 18+ gate, and account deletion. A landing page, signup, login and a profile onboarding step with photo, bio, sports and skill, home area, and an invite setting. Courts, games with reserve and leave, leagues, favorites, follows (mutual follows count as friends), blocking, invites (game, league or short note), and a public profile with stats, major courts and favorite courts. Hosts can record attendance through the API, which feeds the show-up rate.

Not built yet: map view, feed and stories, comments, push or email notifications, an attendance screen, rate limiting, and S3 storage for photos. Photos are saved to `backend/uploads`.

## Run it

You need Python 3.11+, Node 20+, and either Docker or a local MySQL 8.

1. Start MySQL: `docker compose up -d db` (database `pickup`, user `pickup`, password `pickup`).
2. Backend:
   ```
   cd backend
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env             # Windows: copy .env.example .env
   python -m app.seed
   uvicorn app.main:app --reload
   ```
   Tables are created on startup. The seed adds three placeholder courts named "(replace me)".
3. Frontend, in a second terminal:
   ```
   cd frontend
   npm install
   npm run dev
   ```
4. Open http://localhost:5173.

In dev, verification and reset emails are printed in the backend terminal. Signup also shows a "Verify now (dev)" link in the app. Interactive API docs are at http://localhost:8000/docs.

## Tests

```
cd backend
pip install -r requirements-dev.txt
pytest
```
The tests run against SQLite, so they need no MySQL. Run `npm run typecheck` in `frontend` for the TypeScript check.

## Layout

`backend/app/models.py` is the schema. Routers are in `backend/app/routers`, and the stats and profile queries are in `services.py`. The frontend proxies `/api` and `/uploads` to port 8000 (see `vite.config.ts`), so cookies stay same-origin.

## Before real users

Switch from `create_all` to Alembic migrations. Add rate limiting on signup, login and invites. Use a real email provider and set `ENV=prod` and `COOKIE_SECURE=true`. Move photos to object storage. Add a report flow and moderation, and write the terms and privacy policy.
