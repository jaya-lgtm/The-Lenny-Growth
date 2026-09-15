import os
import sys
from pathlib import Path
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# Add backend to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.config import get_settings
from app.db.base import Base
from app.db.session import get_db
import app.models  # load models
from app.main import app

settings = get_settings()

# Determine test database URL.
# If running on host, db:5432 maps to localhost:5432
raw_test_db_url = os.environ.get("TEST_DATABASE_URL", settings.test_database_url)
if "db:5432" in raw_test_db_url:
    try:
        chk = create_engine(raw_test_db_url, connect_args={"connect_timeout": 1})
        with chk.connect():
            pass
        test_db_url = raw_test_db_url
    except Exception:
        test_db_url = raw_test_db_url.replace("db:5432", "localhost:5432")
else:
    test_db_url = raw_test_db_url

# Ensure lenny_growth_test database exists
def ensure_test_database_exists(db_url: str):
    try:
        # Connect to default postgres maintenance database
        maintenance_url = db_url.rsplit("/", 1)[0] + "/postgres"
        engine_maint = create_engine(
            maintenance_url,
            isolation_level="AUTOCOMMIT",
            connect_args={"connect_timeout": 2},
        )
        target_db_name = db_url.rsplit("/", 1)[1].split("?")[0]
        with engine_maint.connect() as conn:
            exists = conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{target_db_name}'")
            ).scalar()
            if not exists:
                conn.execute(text(f"CREATE DATABASE {target_db_name}"))
    except Exception as e:
        # If unable to connect to maintenance db, fallback gracefully
        pass

ensure_test_database_exists(test_db_url)

test_engine = create_engine(test_db_url, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensure vector extension and schema exist in test database."""
    try:
        with test_engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
        Base.metadata.create_all(bind=test_engine)
        yield
        Base.metadata.drop_all(bind=test_engine)
    except Exception as e:
        yield


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a transactional database session per test that rolls back."""
    try:
        connection = test_engine.connect()
        transaction = connection.begin()
        session = TestingSessionLocal(bind=connection)

        yield session

        session.close()
        transaction.rollback()
        connection.close()
    except Exception:
        yield None


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient with overridden get_db dependency."""
    if db_session is not None:
        def _override_get_db():
            try:
                yield db_session
            finally:
                pass
        app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
