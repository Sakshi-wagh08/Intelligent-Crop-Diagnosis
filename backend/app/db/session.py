import os
import socket
from typing import Generator, Tuple, Optional
from unittest.mock import patch
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from backend.app.core.config import settings
from backend.app.core.logging import logger


def _is_server_reachable(host: str, port: int, timeout: float = 0.3) -> bool:
    """Rapid non-blocking IPv4 port probe to verify whether the target database server is listening."""
    target_host = "127.0.0.1" if host in ("localhost", "127.0.0.1") else host
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((target_host, port))
        s.close()
        return True
    except (socket.timeout, OSError, ConnectionRefusedError):
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass


configured_url = settings.get_database_url
using_local_sqlite_fallback = False

if "postgres" in configured_url and not _is_server_reachable(settings.POSTGRES_HOST, settings.POSTGRES_PORT):
    os.makedirs("data", exist_ok=True)
    database_url = "sqlite:///./data/crop_diagnosis_local.db"
    using_local_sqlite_fallback = True
    logger.warning(
        "PostgreSQL at %s:%s is offline. Switching automatically to local seeded SQLite fallback (%s).",
        settings.POSTGRES_HOST,
        settings.POSTGRES_PORT,
        database_url,
    )
else:
    database_url = configured_url

# Configure connection arguments
connect_args = {}
if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif "postgres" in database_url:
    # Set a fast 1-second connect timeout to prevent hangs when server is offline
    connect_args = {"connect_timeout": 1}

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_size=10 if not database_url.startswith("sqlite") else 5,
    max_overflow=20 if not database_url.startswith("sqlite") else 0,
    connect_args=connect_args
)

if database_url.startswith("sqlite"):
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def register_sqlite_gis_functions(dbapi_conn, record):
        def passthrough(val, *args):
            return val
        functions = [
            ("AsEWKB", 1), ("GeomFromEWKT", 1), ("ST_GeomFromEWKT", 1),
            ("GeomFromText", 1), ("GeomFromText", 2),
            ("ST_GeomFromText", 1), ("ST_GeomFromText", 2),
            ("ST_AsBinary", 1), ("ST_AsText", 1),
        ]
        for fn_name, arity in functions:
            try:
                dbapi_conn.create_function(fn_name, arity, passthrough)
            except Exception:
                pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def ensure_local_database_seeded() -> None:
    """Initializes and seeds the local SQLite fallback database if empty."""
    if not database_url.startswith("sqlite"):
        return
    try:
        from backend.app.db.base import Base
        from backend.app.db.seed_data import seed_database
        from backend.app.models.merchant import Merchant
        import backend.app.models  # noqa: F401

        with patch("geoalchemy2.admin.dialects.sqlite.after_create", lambda table, bind, **kw: None):
            with patch("geoalchemy2.admin.dialects.sqlite.before_create", lambda table, bind, **kw: None):
                Base.metadata.create_all(bind=engine)

        db = SessionLocal()
        try:
            if db.query(Merchant).count() == 0:
                seed_database(db)
            else:
                # Ensure any newly added seed entries (e.g., fertilizers) are present
                seed_database(db)
        finally:
            db.close()
    except Exception as exc:
        logger.warning(f"Local SQLite auto-seed warning: {exc}")


def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency providing a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> Tuple[bool, Optional[str]]:
    """Checks whether the active database (PostgreSQL or local SQLite fallback) is reachable."""
    if "postgres" in database_url:
        if not _is_server_reachable(settings.POSTGRES_HOST, settings.POSTGRES_PORT):
            msg = f"Cannot reach PostgreSQL at {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}. Server offline."
            return False, msg

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        if using_local_sqlite_fallback:
            return True, "Local SQLite fallback active (PostgreSQL offline)"
        return True, None
    except Exception as exc:
        logger.warning(f"Database connection check failed: {exc}")
        return False, str(exc)


def check_postgis_extension() -> Tuple[bool, Optional[str]]:
    """Verifies whether the PostGIS spatial extension is installed and active."""
    if database_url.startswith("sqlite"):
        return False, "SQLite Haversine spatial search active (PostGIS unavailable on SQLite)"

    if "postgres" in database_url:
        if not _is_server_reachable(settings.POSTGRES_HOST, settings.POSTGRES_PORT):
            return False, "Database server offline."

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT postgis_full_version();"))
            row = result.fetchone()
            if row:
                return True, str(row[0])
            return False, "PostGIS returned empty version."
    except Exception as exc:
        logger.warning(f"PostGIS extension check failed: {exc}")
        return False, str(exc)
