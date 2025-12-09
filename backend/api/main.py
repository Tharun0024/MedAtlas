"""
FastAPI main application for MedAtlas.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from backend.api.endpoints import providers, validate, discrepancies, export

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MedAtlas API",
    description="AI-powered Provider Data Validation & Directory Management Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(providers.router, prefix="/api", tags=["providers"])
app.include_router(validate.router, prefix="/api", tags=["validation"])
app.include_router(discrepancies.router, prefix="/api", tags=["discrepancies"])
app.include_router(export.router, prefix="/api", tags=["export"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "MedAtlas API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import sys
    from pathlib import Path
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

