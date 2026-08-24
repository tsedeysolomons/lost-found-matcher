"""
Database connection and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL

# Create database engine with explicit enum handling for PostgreSQL
engine = create_engine(
    DATABASE_URL,
    # These settings help with PostgreSQL enum types
    connect_args={
        "options": "-c timezone=utc"
    }
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()

def get_db():
    """
    Dependency function for FastAPI to get database sessions.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
