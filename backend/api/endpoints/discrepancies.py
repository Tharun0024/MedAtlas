"""
Discrepancy endpoints for MedAtlas API.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging
from backend.models import Discrepancy
from backend.database import get_discrepancies, get_provider

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/discrepancies", response_model=List[Discrepancy])
async def get_discrepancies_endpoint(
    provider_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None)
):
    """
    Get discrepancies, optionally filtered by provider_id or status.
    
    Args:
        provider_id: Optional provider ID filter
        status: Optional status filter ('open', 'resolved', etc.)
        
    Returns:
        List of discrepancies
    """
    try:
        discrepancies = get_discrepancies(provider_id=provider_id, status=status)
        return [Discrepancy(**d) for d in discrepancies]
    
    except Exception as e:
        logger.error(f"Error getting discrepancies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discrepancies/{discrepancy_id}", response_model=Discrepancy)
async def get_discrepancy(discrepancy_id: int):
    """
    Get a specific discrepancy by ID.
    
    Args:
        discrepancy_id: Discrepancy ID
        
    Returns:
        Discrepancy object
    """
    from backend.database import get_db_connection
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM discrepancies WHERE id = ?", (discrepancy_id,))
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Discrepancy not found")
            
            return Discrepancy(**dict(row))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting discrepancy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/discrepancies/{discrepancy_id}")
async def update_discrepancy(discrepancy_id: int, status: Optional[str] = None, notes: Optional[str] = None):
    """
    Update a discrepancy (e.g., mark as resolved).
    
    Args:
        discrepancy_id: Discrepancy ID
        status: New status
        notes: Optional notes
        
    Returns:
        Updated discrepancy
    """
    from backend.database import get_db_connection
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if status:
                updates.append("status = ?")
                params.append(status)
            
            if notes:
                updates.append("notes = ?")
                params.append(notes)
            
            if not updates:
                raise HTTPException(status_code=400, detail="No updates provided")
            
            params.append(discrepancy_id)
            query = f"UPDATE discrepancies SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Discrepancy not found")
            
            # Return updated discrepancy
            cursor.execute("SELECT * FROM discrepancies WHERE id = ?", (discrepancy_id,))
            row = cursor.fetchone()
            return Discrepancy(**dict(row))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating discrepancy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

