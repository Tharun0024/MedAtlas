"""
Provider endpoints for MedAtlas API.
"""

from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from typing import List, Dict
import os
import logging
import tempfile
import shutil
import pandas as pd

from backend.models import Provider, SummaryStats
from backend.database import (
    insert_provider,
    get_provider,
    get_all_providers,
    get_provider_by_npi,
    log_event,
)
from backend.main import PipelineOrchestrator

router = APIRouter()
logger = logging.getLogger(__name__)

# Create uploads directory (optional, still kept)
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

orchestrator = PipelineOrchestrator()


@router.post("/providers/upload")
async def upload_providers(
    file: UploadFile = File(...),                       # CSV
    pdf_files: List[UploadFile] = File(default=[]),     # optional PDFs
    run_validation: bool = Form(True),
):
    """
    Upload provider CSV + optional PDFs and run the 4‑agent validation pipeline.

    - CSV rows are processed by PipelineOrchestrator.process_from_csv
      (which internally uses DataValidationAgent, EnrichmentAgent,
       QAAgent, DirectoryManagementAgent).
    - pdf_files are saved and mapped by filename (without extension) to NPI.
    """
    try:
        # --- save CSV to a temp dir ---
        tmp_dir = tempfile.mkdtemp()
        csv_path = os.path.join(tmp_dir, file.filename)
        with open(csv_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # --- save PDFs and build {npi_like: path} mapping ---
        pdf_paths: Dict[str, str] = {}
        for pdf in pdf_files:
            if pdf.content_type != "application/pdf":
                continue
            pdf_path = os.path.join(tmp_dir, pdf.filename)
            with open(pdf_path, "wb") as f:
                shutil.copyfileobj(pdf.file, f)
            # assume filename like "1234567890.pdf" where 1234567890 is NPI
            npi_key = os.path.splitext(pdf.filename)[0]
            pdf_paths[npi_key] = pdf_path

        # --- call orchestrator (validation agent lives inside this) ---
        if run_validation:
            results = await orchestrator.process_from_csv(
                csv_path=csv_path,
                pdf_paths=pdf_paths or None,
            )
        else:
            # if someone disables validation, still use orchestrator but ignore PDFs
            results = await orchestrator.process_from_csv(csv_path=csv_path)

        imported_count = len(results)

        log_event(
            "upload",
            f"Uploaded and processed {imported_count} providers from {file.filename}",
            None,
        )
        return {"uploaded": imported_count, "processed": imported_count}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}")
        raise HTTPException(status_code=500, detail="Upload and validation failed")


@router.get("/providers")
async def get_providers():
    """
    Get all providers from SQLite.
    Returns simplified JSON with: id, name, specialty, phone, status, confidence_score.
    Returns empty list if no data (not error).
    """
    try:
        providers = get_all_providers(limit=10000, offset=0)

        result = []
        for p in providers:
            name = ""
            if p.get("first_name") or p.get("last_name"):
                name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
            if not name and p.get("organization_name"):
                name = p.get("organization_name")
            if not name:
                name = "Unknown"

            result.append(
                {
                    "id": p.get("id"),
                    "name": name,
                    "specialty": p.get("specialty") or "N/A",
                    "phone": p.get("phone") or "N/A",
                    "status": p.get("validation_status") or "pending",
                    "confidence_score": p.get("confidence_score") or 0,
                }
            )

        return result

    except Exception as e:
        logger.error(f"Error getting providers: {e}")
        return []


@router.get("/provider/{provider_id}", response_model=Provider)
async def get_provider_by_id(provider_id: int):
    """
    Get a specific provider by ID.
    """
    provider = get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    return Provider(**provider)


@router.get("/summary", response_model=SummaryStats)
async def get_summary_stats():
    """
    Get summary statistics.
    """
    try:
        all_providers = get_all_providers(limit=10000)

        total = len(all_providers)
        validated = len(
            [p for p in all_providers if p.get("validation_status") == "validated"]
        )
        pending = len(
            [p for p in all_providers if p.get("validation_status") == "pending"]
        )

        confidence_scores = [p.get("confidence_score", 0) for p in all_providers]
        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores
            else 0
        )

        high_risk = len([p for p in all_providers if p.get("risk_score", 0) >= 70])

        from backend.database import get_discrepancies

        all_discrepancies = get_discrepancies()
        total_disc = len(all_discrepancies)
        open_disc = len([d for d in all_discrepancies if d.get("status") == "open"])

        return SummaryStats(
            total_providers=total,
            validated_providers=validated,
            pending_providers=pending,
            total_discrepancies=total_disc,
            open_discrepancies=open_disc,
            avg_confidence_score=round(avg_confidence, 2),
            high_risk_providers=high_risk,
        )

    except Exception as e:
        logger.error(f"Error getting summary stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
