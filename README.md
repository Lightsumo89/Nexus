<a id="readme-top"></a>

# Nexus

A sports discovery and community platform that connects players, courts, and organized games.

[Report a Bug](../../issues/new) · [Request a Feature](../../issues/new)

Status: early prototype, running locally. Last updated: 2026-11-15.

## Table of Contents

1. [About the Project](#about-the-project)
2. [Built With](#built-with)
3. [Getting Started](#getting-started)
4. [Usage](#usage)
5. [Repository Structure](#repository-structure)
6. [Roadmap](#roadmap)
7. [Contributing](#contributing)
8. [License](#license)
9. [Contact](#contact)

## About the Project

![Nexus screenshot](docs/screenshot.png)

Finding a pickup game usually means a group chat and some guesswork. Nexus puts courts on a map, lets players create and join games, and ties it together with profiles and follows, so organizing a game takes a few taps instead of a dozen messages. Longer term it aims to serve organizers, leagues, private venues, and municipal facilities.

Current features:

- Registration, login, email verification, and password recovery
- Profiles, following and unfollowing users
- Court discovery on a map
- Game creation, scheduling, joining, leaving, cancellation, and host transfer
- Personal game listings
- Basic leagues

In progress: user search, invitation workflows with expiration, creating a game from an existing attendee list, minimum-player requirements with automatic cancellation, and roster management.

<p align="right"><a href="#readme-top">back to top</a></p>

## Built With

| Layer | Tools |
| --- | --- |
| Frontend | React, TypeScript, Vite, React Query, React Router |
| Backend | Python, FastAPI, SQLAlchemy, Uvicorn |
| Database | MySQL (SQLite supported for development and tests) |

The frontend calls a JSON HTTP API served by FastAPI, and SQLAlchemy maps the backend models to the database. Tested with Python TODO, Node TODO, and MySQL TODO.

<p align="right"><a href="https://github.com/Lightsumo89/Nexus.git">back to top</a></p>

## Getting Started

### Prerequisites

Python 3, Node.js with npm, MySQL, and Git.

### Installation

1. Clone the repo and enter it.

```bash
git clone <repository-url>
cd Nexus
```

2. Create an empty MySQL database and a user with access to it.

3. Set up the backend.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

4. Edit `backend/.env` with your database and email settings (see [Configuration](#configuration)).

5. Seed the database and start the API.

```bash
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

The API runs at `http://127.0.0.1:8000` with interactive docs at `http://127.0.0.1:8000/docs`.

6. In a second terminal, start the frontend.

```bash
cd frontend
npm install
npm run dev
```

Open the address Vite prints in the terminal.

### Configuration

All secrets live in `backend/.env`, which is git-ignored. `.env.example` lists every variable the app reads.

| Setting | Purpose |
| --- | --- |
| Database connection | MySQL (or SQLite for development) |
| App environment | Development or production behavior |
| Session and auth | Token signing and session lifetime |
| Email credentials | Verification and password recovery emails |
| File uploads | Profile image storage |

Never commit real credentials.

<p align="right"><a href="#readme-top">back to top</a></p>

## Usage

With everything running, you can:

1. Register an account and verify your email.
2. Complete your profile.
3. Browse courts on the map.
4. Create a game, or join or leave someone else's.
5. Manage a game you host, including transferring the host role.
6. View your games and follow other players.

<p align="right"><a href="#readme-top">back to top</a></p>

## Repository Structure

```text
Nexus/
├── backend/app/
│   ├── routers/
│   │   ├── auth.py        registration, login, verification, recovery
│   │   ├── courts.py      court and facility endpoints
│   │   ├── games.py       game creation, joining, hosting
│   │   ├── invites.py     game invitations
│   │   ├── leagues.py     league endpoints
│   │   ├── me.py          current-user profile and activity
│   │   └── users.py       user lookup and follows
│   ├── config.py          settings loaded from the environment
│   ├── db.py              database engine and sessions
│   ├── deps.py            shared request dependencies
│   ├── mailer.py          outgoing email
│   ├── main.py            FastAPI app entry point
│   ├── models.py          SQLAlchemy models
│   ├── schemas.py         request and response schemas
│   ├── security.py        password hashing and tokens
│   ├── seed.py            sample data
│   └── services.py        business logic
├── frontend/src/
│   ├── components/        reusable UI components
│   ├── pages/             route-level pages
│   ├── api.ts             backend API client
│   ├── App.tsx            app shell and routing
│   ├── hooks.ts           shared hooks
│   └── types.ts           shared TypeScript types
└── README.md
```

<p align="right"><a href="#readme-top">back to top</a></p>

## Roadmap

- [x] Accounts, profiles, follows
- [x] Court discovery and map
- [x] Game creation, joining, and host transfer
- [ ] Invitations, rosters, minimum-player cancellation
- [ ] User search and discovery
- [ ] Activity feed, direct messaging, event chats, teams and private groups
- [ ] Leagues, tournaments, free-agent registration, player stats
- [ ] Private venue booking, payments and splitting, digital waivers
- [ ] Municipal facility scheduling, occupancy, and utilization reporting

Priorities shift with testing and feedback.

<p align="right"><a href="#readme-top">back to top</a></p>

## Contributing

This is a private project and contributions happen through repository access granted by the owner. Coordinate larger changes first, test locally, and document any new dependency or config variable. Report security issues privately to the owner, not in issues or commits.

## License

Proprietary. All rights reserved. Repository access doesn't grant permission to copy, modify, redistribute, or commercially use the software.

## Contact

Jack - TODO email - Project link: TODO repository URL

<p align="right"><a href="#readme-top">back to top</a></p>
