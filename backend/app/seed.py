from sqlalchemy import func, select

from .db import Base, SessionLocal, engine
from .models import Court

SAMPLE = [
    ("Sample Court 1 (replace me)", "basketball", 42.3955, -71.1020, "07:00", "22:00"),
    ("Sample Court 2 (replace me)", "basketball", 42.3875, -71.0950, "07:00", "21:00"),
    ("Sample Field 1 (replace me)", "soccer", 42.3990, -71.0830, "08:00", "21:00"),
]


def run() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(Court)):
            print("Courts already exist, skipping seed")
            return
        for name, sport, lat, lng, opens, closes in SAMPLE:
            db.add(Court(name=name, sport=sport, lat=lat, lng=lng, opens=opens, closes=closes))
        db.commit()
        print(f"Seeded {len(SAMPLE)} sample courts")


if __name__ == "__main__":
    run()
