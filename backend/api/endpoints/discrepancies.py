"""
Discrepancy endpoints for MedAtlas API.
"""

import logging
from typing import List, Optional, Any

from fastapi import APIRouter, HTTPException, Query

from backend.models import (
    Discrepancy,
    make_discrepancy,
    DiscrepancyUpdate,
)
from backend.database import get_discrepancies, get_provider

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/discrepancies", response_model=List[Discrepancy])
async def get_discrepancies_endpoint(
    provider_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
):
    """
    Get discrepancies, optionally filtered by provider_id or status.
    """
    try:
        rows = get_discrepancies(provider_id=provider_id, status=status)

        # rows may be dicts or DB row objects; normalize to dict first
        result: List[Discrepancy] = []
        for row in rows:
            data = dict(row) if not isinstance(row, dict) else row
            result.append(make_discrepancy(data))

        return result
    except Exception as e:
        logger.error(f"Error getting discrepancies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discrepancies/{discrepancy_id}", response_model=Discrepancy)
async def get_discrepancy(discrepancy_id: int):
    """
    Get a specific discrepancy by ID.
    """
    from backend.database import get_db_connection

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM discrepancies WHERE id = ?",
                (discrepancy_id,),
            )
            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Discrepancy not found")

            data = dict(row) if not isinstance(row, dict) else row
            return make_discrepancy(data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting discrepancy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/discrepancies/{discrepancy_id}", response_model=Discrepancy)
async def update_discrepancy(discrepancy_id: int, body: DiscrepancyUpdate):
    """
    Update a discrepancy (e.g., mark as resolved).

    The frontend sends JSON like:
      { "status": "resolved", "notes": "Resolved manually" }
    """
    from backend.database import get_db_connection

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            updates: List[str] = []
            params: List[Any] = []

            if body.status is not None:
                updates.append("status = ?")
                params.append(body.status)

            if body.notes is not None:
                updates.append("notes = ?")
                params.append(body.notes)

            if not updates:
                raise HTTPException(status_code=400, detail="No updates provided")

            params.append(discrepancy_id)
            query = f"UPDATE discrepancies SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Discrepancy not found")

            # Return updated discrepancy
            cursor.execute(
                "SELECT * FROM discrepancies WHERE id = ?",
                (discrepancy_id,),
            )
            row = cursor.fetchone()
            data = dict(row) if not isinstance(row, dict) else row
            return make_discrepancy(data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating discrepancy: {e}")
        raise HTTPException(status_code=500, detail=str(e))
