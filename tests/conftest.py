from typing import Generator
import pytest
from unittest.mock import patch
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.db.seed_data import seed_database
from backend.app.main import app
import backend.app.models  # Register all models


# In-memory SQLite Engine with StaticPool for test suite isolation
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)


# Register SQLite mock PostGIS functions for test-suite execution without external SpatiaLite C-libraries
@event.listens_for(test_engine, "connect")
def register_sqlite_gis_functions(dbapi_conn, record):
    """Registers lightweight spatial dummy functions on SQLite connections."""
    def passthrough(val, *args):
        return val

    functions = [
        ("AsEWKB", 1),
        ("GeomFromEWKT", 1),
        ("ST_GeomFromEWKT", 1),
        ("GeomFromText", 1),
        ("GeomFromText", 2),
        ("ST_GeomFromText", 1),
        ("ST_GeomFromText", 2),
        ("ST_AsBinary", 1),
        ("ST_AsText", 1),
    ]
    for fn_name, arity in functions:
        try:
            dbapi_conn.create_function(fn_name, arity, passthrough)
        except Exception:
            pass


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Initializes in-memory test database tables and seeds demo records."""
    # Patch GeoAlchemy2 sqlite event listeners that expect SpatiaLite C extension
    with patch("geoalchemy2.admin.dialects.sqlite.after_create", lambda table, bind, **kw: None):
        with patch("geoalchemy2.admin.dialects.sqlite.before_create", lambda table, bind, **kw: None):
            Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    yield

    with patch("geoalchemy2.admin.dialects.sqlite.after_drop", lambda table, bind, **kw: None):
        with patch("geoalchemy2.admin.dialects.sqlite.before_drop", lambda table, bind, **kw: None):
            Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def mock_db_health_checks(monkeypatch):
    """Bypasses external PostgreSQL socket probes during test execution using in-memory SQLite."""
    monkeypatch.setattr("backend.app.main.check_database_connection", lambda: (True, "SQLite memory test db"))
    monkeypatch.setattr("backend.app.main.check_postgis_extension", lambda: (True, "POSTGIS=3.4.0 (mock)"))


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provides a transactional database session for tests."""
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Provides a FastAPI TestClient with the database session overridden."""
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
