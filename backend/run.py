"""
Development server runner.
Simpler alternative to uvicorn command.
"""
import uvicorn
from app.config import ENVIRONMENT

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=ENVIRONMENT == "development",
        log_level="info"
    )
