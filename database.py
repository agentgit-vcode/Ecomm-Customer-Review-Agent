"""Database engine and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///data/reviewiq.db"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_session():
    """Get a new database session."""
    return SessionLocal()


def init_db():
    """Create all tables if they don't exist."""
    import models  # noqa: F401 — registers models with Base
    Base.metadata.create_all(engine)
