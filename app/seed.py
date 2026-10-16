"""Insert demo passengers and drivers without replacing existing records."""

from uuid import UUID

from sqlalchemy.dialects.postgresql import insert

from app.dependencies import SessionLocal
from app.models import Driver, Passenger


def seed_demo_data() -> None:
    with SessionLocal.begin() as db:
        db.execute(
            insert(Passenger).on_conflict_do_nothing(index_elements=["id"]),
            [
                {"id": UUID(int=1), "name": "Alex"},
                {"id": UUID(int=2), "name": "Morgan"},
            ],
        )
        db.execute(
            insert(Driver).on_conflict_do_nothing(index_elements=["id"]),
            [
                {"id": UUID(int=3), "name": "Sam", "vehicle_registration": "1234 ABC"},
                {
                    "id": UUID(int=4),
                    "name": "Riley",
                    "vehicle_registration": "5678 DEF",
                },
            ],
        )


if __name__ == "__main__":
    seed_demo_data()
