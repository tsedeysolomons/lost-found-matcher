"""
Database initialization script.
Run this after setting up PostgreSQL to create tables.
"""
from app.database import engine, Base
from app.models.report import Report
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """
    Initialize database tables.
    This will create all tables defined in SQLAlchemy models.
    """
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables created successfully!")
        logger.info("✓ Ready to use")
    except Exception as e:
        logger.error(f"✗ Error creating database tables: {e}")
        logger.error("Make sure PostgreSQL is running and pgvector extension is installed")
        raise

if __name__ == "__main__":
    init_database()
