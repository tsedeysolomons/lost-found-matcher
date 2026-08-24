"""
Main FastAPI application for Lost and Found Matching System.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.api import reports
from app.database import engine, Base
from app.config import CORS_ORIGINS, ENVIRONMENT, LOG_LEVEL

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Lost and Found Matching API",
    description="Hybrid matching system for lost and found items using semantic embeddings",
    version="1.0.0",
    docs_url="/docs" if ENVIRONMENT == "development" else None
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(reports.router)

@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "message": "Lost and Found Matching API",
        "status": "operational",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=ENVIRONMENT == "development"
    )
