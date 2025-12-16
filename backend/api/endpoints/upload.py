"""
Upload endpoints for MedAtlas API.

Handles CSV + optional PDF uploads and runs the 4‑agent pipeline.
"""

from typing import List, Dict

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import logging
import os
import shutil
import tempfile

from backend.pipeline.main import PipelineOrchestrator

router = APIRouter()
logger = logging.getLogger(__name__)

orchestrator = PipelineOrchestrator()


@router.post("/providers/upload")
async def upload_providers(
    csv_file: UploadFile = File(...),
    pdf_files: List[UploadFile] = File(default=[]),
    run_validation: bool = Form(True),
):
    """
    Upload provider CSV + optional PDFs and process through the pipeline.

    Body (multipart/form-data):
        csv_file: CSV file with provider records (required)
        pdf_files: One or more PDF files (optional, repeated field)
        run_validation: Whether to run validation immediately (currently informational)
    """
    try:
        # Basic validation on CSV
        if csv_file.content_type not in ("text/csv", "application/vnd.ms-excel"):
            raise HTTPException(status_code=400, detail="csv_file must be a CSV")

        # Create temporary directory
        tmp_dir = tempfile.mkdtemp()

        # Save CSV
        csv_path = os.path.join(tmp_dir, csv_file.filename)
        with open(csv_path, "wb") as f:
            shutil.copyfileobj(csv_file.file, f)

        # Save PDFs and build {NPI-ish: path} mapping
        pdf_paths: Dict[str, str] = {}
        for pdf in pdf_files:
            if pdf.content_type != "application/pdf":
                # ignore non‑PDFs silently; could also raise
                continue

            pdf_path = os.path.join(tmp_dir, pdf.filename)
            with open(pdf_path, "wb") as f:
                shutil.copyfileobj(pdf.file, f)

            # Simple heuristic: use filename (without extension) as key,
            # e.g. "1234567890.pdf" -> "1234567890" (expected NPI)
            npi_key = os.path.splitext(pdf.filename)[0]
            pdf_paths[npi_key] = pdf_path

        # Run pipeline from CSV using your orchestrator
        results = await orchestrator.process_from_csv(
            csv_path=csv_path,
            pdf_paths=pdf_paths or None,
        )

        imported_count = len(results) if results is not None else 0

        # Optionally you can add a real validation_run_id if you track jobs
        return {
            "imported_count": imported_count,
            "validation_run_id": None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error uploading providers: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")
