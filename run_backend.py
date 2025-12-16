"""
Backend startup script for MedAtlas.
Adds project root to Python path and starts the FastAPI server.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import uvicorn
    from MedAtlas.backend.main import app
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

