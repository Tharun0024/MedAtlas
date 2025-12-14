"""
Validation endpoints for MedAtlas API.
"""

from fastapi import APIRouter, HTTPException, File, UploadFile
from typing import Optional
import logging
import os
from backend.models import ValidationRequest, ValidationResult
from backend.database import get_provider, get_provider_by_npi, log_event
from backend.agents import DataValidationAgent
from backend.ocr import extract_from_pdf_bytes

router = APIRouter()
logger = logging.getLogger(__name__)

# Create uploads directory for PDFs
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)


@router.post("/validate")
async def validate_all_providers():
    """
    Run validation pipeline for all providers.
    - Updates provider status (validated/needs_review)
    - Stores discrepancies in discrepancies table
    - Updates confidence score (0-100)
    """
    try:
        # import sys
        # from pathlib import Path
        # # Adds project root to path
        # project_root = Path(__file__).parent.parent.parent.parent
        # sys.path.insert(0, str(project_root))
        
        from backend.pipeline import run_validation_pipeline
        result = await run_validation_pipeline()
        return result
    
    except Exception as e:
        logger.error(f"Error running validation pipeline: {e}", exc_info=True)
        # import traceback
        # logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-provider")
async def validate_single_provider(request: ValidationRequest):
    """
    Validate provider(s) using the main validation pipeline.
    Mini-project version: runs full pipeline to ensure DB is updated.
    """
    try:
        from backend.pipeline import run_validation_pipeline

        # Run pipeline (updates DB)
        result = await run_validation_pipeline()

        return {
            "status": "success",
            "message": "Validation completed",
            "result": result
        }

    except Exception as e:
        logger.error(f"Error validating provider: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Validation failed")



@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file for OCR extraction.
    
    Args:
        file: PDF file
        
    Returns:
        Extracted text and structured data
    """
    try:
        # Read file content
        content = await file.read()
        
        # Extract text using OCR
        result = extract_from_pdf_bytes(content)
        
        return {
            "success": result.get("success", False),
            "text": result.get("full_text", ""),
            "structured_data": result.get("structured_data", {}),
            "page_count": result.get("page_count", 0)
        }
    
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

