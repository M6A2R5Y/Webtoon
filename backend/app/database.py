"""
Database connection setup using SQLAlchemy.

Mentor Note:
- During local development, `DATABASE_URL` defaults to `sqlite:///./studio.db`.
- When deploying to production (e.g., Render, Railway, Supabase, Neon), you only need
  to set `DATABASE_URL=postgresql://user:pass@host:5432/dbname` in your environment.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# SQLite requires `check_same_thread=False` when used with FastAPI's async/multi-threaded requests.
# PostgreSQL does not need or accept `check_same_thread`.
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a database session for a single request and closes it safely."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
