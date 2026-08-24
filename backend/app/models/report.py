"""
SQLAlchemy ORM model for Report entity.
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, Text
from sqlalchemy.dialects.postgresql import ARRAY
from pgvector.sqlalchemy import Vector
from datetime import datetime
import enum
from app.database import Base
from app.config import EMBEDDING_DIMENSION

class ReportType(str, enum.Enum):
    """Enum for report types."""
    LOST = "Lost"
    FOUND = "Found"

class ReportStatus(str, enum.Enum):
    """Enum for report status."""
    SEARCHING = "Searching"
    UNCLAIMED = "Unclaimed"
    RESOLVED = "Resolved"

class Report(Base):
    """
    Report model representing a lost or found item.
    """
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(ReportType), nullable=False, index=True)
    item = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    color = Column(String(100), nullable=False)
    location = Column(String(500), nullable=False)
    date = Column(Date, nullable=False, index=True)
    status = Column(
        Enum(ReportStatus), 
        nullable=False, 
        default=ReportStatus.SEARCHING
    )
    details = Column(Text, nullable=True)
    
    # Embedding vector (384 dimensions for all-MiniLM-L6-v2)
    embedding = Column(Vector(EMBEDDING_DIMENSION), nullable=True)
    
    # Extracted keywords for fast matching
    keywords = Column(ARRAY(String), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<Report(id={self.id}, type={self.type}, item={self.item})>"
