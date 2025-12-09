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
    
    This endpoint:
    - Loads all providers from DB
    - For each provider, triggers pipeline:
      - DataValidationAgent
      - EnrichmentAgent
      - QAAgent
      - DirectoryAgent
    - Updates provider status (validated/needs_review)
    - Stores discrepancies in discrepancies table
    - Updates confidence score (0-100)
    
    Returns:
        {
          "status": "success",
          "validated": <count>,
          "needs_review": <count>
        }
    """
    try:
        import sys
        from pathlib import Path
        # Add project root to path
        project_root = Path(__file__).parent.parent.parent.parent
        sys.path.insert(0, str(project_root))
        
        from backend.main import run_validation_pipeline
        
        result = await run_validation_pipeline()
        
        return result
    
    except Exception as e:
        logger.error(f"Error running validation pipeline: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-provider", response_model=ValidationResult)
async def validate_single_provider(request: ValidationRequest):
    """
    Validate a single provider through the validation pipeline.
    
    Args:
        request: Validation request with provider_id or npi
        
    Returns:
        Validation result with confidence scores and discrepancies
    """
    try:
        # Get provider
        if request.provider_id:
            provider = get_provider(request.provider_id)
        elif request.npi:
            provider = get_provider_by_npi(request.npi)
        else:
            raise HTTPException(status_code=400, detail="Either provider_id or npi must be provided")
        
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        # Skip validation if already validated and not forcing revalidation
        if not request.force_revalidate and provider.get("validation_status") == "validated":
            from backend.database import get_discrepancies
            discrepancies = get_discrepancies(provider_id=provider["id"])
            
            return ValidationResult(
                provider_id=provider["id"],
                validated=True,
                confidence_score=provider.get("confidence_score", 0),
                discrepancies=discrepancies,
                validated_data=provider.get("validated_data", {})
            )
        
        # Run validation agent
        validation_agent = DataValidationAgent()
        validation_results = await validation_agent.validate_provider(provider)
        
        # Get discrepancies
        from backend.database import get_discrepancies
        discrepancies = get_discrepancies(provider_id=provider["id"])
        
        return ValidationResult(
            provider_id=provider["id"],
            validated=validation_results.get("npi_valid", False),
            confidence_score=sum(validation_results.get("confidence_scores", {}).values()) // 
                           max(len(validation_results.get("confidence_scores", {})), 1),
            discrepancies=discrepancies,
            validated_data=validation_results.get("validated_data", {})
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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

