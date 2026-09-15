from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import get_settings

settings = get_settings()

db_url = settings.database_url
if "db:5432" in db_url:
    try:
        chk = create_engine(db_url, connect_args={"connect_timeout": 1})
        with chk.connect():
            pass
    except Exception:
        db_url = db_url.replace("db:5432", "localhost:5432")

engine = create_engine(
    db_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
