"""
Validation endpoints for MedAtlas API.
"""

from fastapi import APIRouter, HTTPException, File, UploadFile
import logging
import os

from backend.models import ValidationRequest
from backend.ocr import extract_from_pdf_bytes
from backend.main import PipelineOrchestrator  # orchestrator with 4 agents

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

orchestrator = PipelineOrchestrator()


@router.post("/validate")
async def validate_all_providers():
    """
    Run validation pipeline for all providers.
    """
    try:
        from backend.pipeline import run_validation_pipeline
        result = await run_validation_pipeline()
        return result
    except Exception as e:
        logger.error(f"Error running validation pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/provider/{provider_id}/validate")
async def validate_single_provider(provider_id: int):
    """
    Run full 4‑agent pipeline for a single provider.
    """
    try:
        result = await orchestrator.process_provider(provider_id)
        return result
    except Exception as e:
        logger.error(f"Error validating provider {provider_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Validation failed")


@router.post("/validate-provider")
async def validate_single_provider_legacy(request: ValidationRequest):
    """
    Legacy endpoint – still runs full pipeline but ignores request details.
    """
    try:
        from backend.pipeline import run_validation_pipeline
        result = await run_validation_pipeline()
        return {
            "status": "success",
            "message": "Validation completed",
            "result": result,
        }
    except Exception as e:
        logger.error(f"Error validating provider: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Validation failed")


@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file for OCR extraction.
    """
    try:
        content = await file.read()
        result = extract_from_pdf_bytes(content)

        return {
            "success": result.get("success", False),
            "text": result.get("full_text", ""),
            "structured_data": result.get("structured_data", {}),
            "page_count": result.get("page_count", 0),
        }
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))
