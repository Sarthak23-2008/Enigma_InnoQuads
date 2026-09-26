"""Create all tables (idempotent). Usage: python -m app.database.init_db"""
from app.database.session import Base, engine
from app import models  # noqa: F401  (registers models)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database tables created.")
