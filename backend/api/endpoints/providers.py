"""
Provider endpoints for MedAtlas API.
"""

from fastapi import APIRouter, HTTPException, Query, File, UploadFile
from typing import List, Optional
import pandas as pd
import os
import logging
from backend.models import Provider, ProviderCreate, UploadResponse, SummaryStats
from backend.database import (
    insert_provider, get_provider, get_all_providers,
    get_provider_by_npi, log_event
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Create uploads directory
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)


@router.post("/upload")
async def upload_providers(file: UploadFile = File(...)):
    """
    Upload provider CSV file and insert rows into SQLite.

    Reads CSV using pandas from the uploaded file object, validates required
    columns, converts rows to provider dicts and inserts them using
    `insert_provider()`.

    Returns: { "uploaded": <number_of_inserted_rows> }
    """
    required_columns = [
        "NPI", "First Name", "Last Name", "Organization Name", "Provider Type",
        "Specialty", "Address Line 1", "Address Line 2", "City", "State",
        "ZIP Code", "Phone", "Email", "Website", "License Number",
        "License State", "Practice Name"
    ]

    try:
        # Read CSV directly from the uploaded file object
        # Ensure the file pointer is at the beginning
        try:
            file.file.seek(0)
        except Exception:
            pass

        df = pd.read_csv(file.file)

        # Validate required columns
        missing = [c for c in required_columns if c not in df.columns]
        if missing:
            msg = f"Missing required columns: {', '.join(missing)}"
            logger.error(msg)
            raise HTTPException(status_code=400, detail=msg)

        inserted = 0
        for _, row in df.iterrows():
            # Build provider dict mapping CSV columns to DB fields
            provider_data = {
                "npi": str(row.get("NPI", "")).strip() if pd.notna(row.get("NPI")) else None,
                "first_name": str(row.get("First Name", "")).strip() if pd.notna(row.get("First Name")) else None,
                "last_name": str(row.get("Last Name", "")).strip() if pd.notna(row.get("Last Name")) else None,
                "organization_name": str(row.get("Organization Name", "")).strip() if pd.notna(row.get("Organization Name")) else None,
                "provider_type": str(row.get("Provider Type", "")).strip() if pd.notna(row.get("Provider Type")) else None,
                "specialty": str(row.get("Specialty", "")).strip() if pd.notna(row.get("Specialty")) else None,
                "address_line1": str(row.get("Address Line 1", "")).strip() if pd.notna(row.get("Address Line 1")) else None,
                "address_line2": str(row.get("Address Line 2", "")).strip() if pd.notna(row.get("Address Line 2")) else None,
                "city": str(row.get("City", "")).strip() if pd.notna(row.get("City")) else None,
                "state": str(row.get("State", "")).strip() if pd.notna(row.get("State")) else None,
                "zip_code": str(row.get("ZIP Code", "")).strip() if pd.notna(row.get("ZIP Code")) else None,
                "phone": str(row.get("Phone", "")).strip() if pd.notna(row.get("Phone")) else None,
                "email": str(row.get("Email", "")).strip() if pd.notna(row.get("Email")) else None,
                "website": str(row.get("Website", "")).strip() if pd.notna(row.get("Website")) else None,
                "license_number": str(row.get("License Number", "")).strip() if pd.notna(row.get("License Number")) else None,
                "license_state": str(row.get("License State", "")).strip() if pd.notna(row.get("License State")) else None,
                "practice_name": str(row.get("Practice Name", "")).strip() if pd.notna(row.get("Practice Name")) else None,
                "source_file": file.filename,
                "raw_data": row.to_dict()
            }

            # Skip if NPI exists in DB
            if provider_data["npi"]:
                existing = get_provider_by_npi(provider_data["npi"])
                if existing:
                    # Update existing provider instead of skipping
                    from backend.database import update_provider
                    update_provider(existing["id"], provider_data)
                    inserted += 1
                    continue


            try:
                insert_provider(provider_data)
                inserted += 1
            except Exception as ie:
                # Log insertion error but continue with other rows
                logger.error(f"Failed to insert provider row (NPI={provider_data.get('npi')}): {ie}")
                continue

        log_event("upload", f"Uploaded {inserted} providers from {file.filename}", None)
        return {"uploaded": inserted}

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def get_providers():
    """
    Get all providers from SQLite.
    Returns simplified JSON with: id, name, specialty, phone, status, confidence_score.
    Returns empty list if no data (not error).
    """
    try:
        providers = get_all_providers(limit=10000, offset=0)
        
        # Transform to simplified format
        result = []
        for p in providers:
            # Build name from first_name + last_name or organization_name
            name = ""
            if p.get("first_name") or p.get("last_name"):
                name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
            if not name and p.get("organization_name"):
                name = p.get("organization_name")
            if not name:
                name = "Unknown"
            
            result.append({
                "id": p.get("id"),
                "name": name,
                "specialty": p.get("specialty") or "N/A",
                "phone": p.get("phone") or "N/A",
                "status": p.get("validation_status") or "pending",
                "confidence_score": p.get("confidence_score") or 0
            })
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting providers: {e}")
        # Return empty list on error, not raise exception
        return []


@router.get("/provider/{provider_id}", response_model=Provider)
async def get_provider_by_id(provider_id: int):
    """
    Get a specific provider by ID.
    
    Args:
        provider_id: Provider ID
        
    Returns:
        Provider object
    """
    provider = get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return Provider(**provider)


@router.get("/summary", response_model=SummaryStats)
async def get_summary_stats():
    """
    Get summary statistics.
    
    Returns:
        Summary statistics
    """
    try:
        all_providers = get_all_providers(limit=10000)
        
        total = len(all_providers)
        validated = len([p for p in all_providers if p.get("validation_status") == "validated"])
        pending = len([p for p in all_providers if p.get("validation_status") == "pending"])
        
        confidence_scores = [p.get("confidence_score", 0) for p in all_providers]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
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
            high_risk_providers=high_risk
        )
    
    except Exception as e:
        logger.error(f"Error getting summary stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

