"""
Configuration settings for the Lost and Found matching system.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/lost_found_db")

# Embedding Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIMENSION = 384  # Dimension for all-MiniLM-L6-v2

# Matching Algorithm Weights
MATCH_WEIGHTS = {
    'item_category': 0.25,
    'vector': 0.25,
    'keywords': 0.15,
    'location': 0.15,
    'color': 0.10,
    'date': 0.10
}

# Fallback weights when embedding unavailable (renormalized to 100%)
FALLBACK_WEIGHTS = {
    'item_category': 0.333,  # 25/75
    'keywords': 0.20,        # 15/75
    'location': 0.20,        # 15/75
    'color': 0.133,          # 10/75
    'date': 0.133            # 10/75
}

# Matching Threshold
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "35.0"))

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
