"""
Export endpoints for MedAtlas API.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import List, Optional
import logging
import os
from backend.models import ExportRequest
from backend.agents import DirectoryManagementAgent

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/export")
async def export_directory(request: ExportRequest):
    """
    Export provider directory.
    
    Args:
        request: Export request with format and filters
        
    Returns:
        Export file information
    """
    try:
        directory_agent = DirectoryManagementAgent()
        result = await directory_agent.export_directory(
            format=request.format,
            provider_ids=request.provider_ids,
            include_discrepancies=request.include_discrepancies
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error exporting directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/download/{filename}")
async def download_export(filename: str):
    """
    Download an exported file.
    
    Args:
        filename: Name of the export file
        
    Returns:
        File download response
    """
    try:
        exports_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports")
        filepath = os.path.join(exports_dir, filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            filepath,
            media_type="application/octet-stream",
            filename=filename
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

