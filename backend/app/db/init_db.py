"""Database Initialization Script.

Creates all database tables, spatial indexes, and seeds baseline demonstration data.
"""

from sqlalchemy import text
from backend.app.db.session import engine, SessionLocal
from backend.app.db.base import Base
from backend.app.db.seed_data import seed_database
from backend.app.core.logging import logger
import backend.app.models  # Ensures all model classes are registered


def init_db(seed: bool = True) -> bool:
    """Initializes the database schema and seeds initial demonstration records."""
    logger.info("Starting database initialization...")

    dialect_name = engine.dialect.name
    logger.info(f"Target Database Dialect: {dialect_name}")

    with engine.begin() as conn:
        if dialect_name == "postgresql":
            logger.info("Enabling PostGIS extension on PostgreSQL...")
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                logger.info("PostGIS extension confirmed.")
            except Exception as e:
                logger.warning(f"Could not enable PostGIS extension directly: {e}")

    logger.info("Creating all database tables via SQLAlchemy metadata...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")

    if seed:
        db = SessionLocal()
        try:
            logger.info("Seeding demonstration agronomic knowledge base & merchants...")
            counts = seed_database(db)
            logger.info(f"Seed completed: {counts}")
        except Exception as e:
            logger.error(f"Error during database seeding: {e}")
            db.rollback()
            raise e
        finally:
            db.close()

    logger.info("Database initialization completed successfully.")
    return True


if __name__ == "__main__":
    init_db(seed=True)
