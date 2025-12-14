"""
Database module for MedAtlas.
Handles SQLite database operations with clean separation for future PostgreSQL migration.
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import os


# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "medatlas.db")


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Initialize database tables."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Providers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS providers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                npi TEXT UNIQUE,
                first_name TEXT,
                last_name TEXT,
                organization_name TEXT,
                provider_type TEXT,
                specialty TEXT,
                address_line1 TEXT,
                address_line2 TEXT,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                phone TEXT,
                email TEXT,
                website TEXT,
                license_number TEXT,
                license_state TEXT,
                practice_name TEXT,
                confidence_score INTEGER DEFAULT 0,
                risk_score INTEGER DEFAULT 0,
                validation_status TEXT DEFAULT 'pending',
                source_file TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_data TEXT,
                validated_data TEXT,
                enriched_data TEXT
            )
        """)
        
        # Discrepancies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS discrepancies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_id INTEGER,
                field_name TEXT,
                csv_value TEXT,
                api_value TEXT,
                scraped_value TEXT,
                final_value TEXT,
                confidence INTEGER,
                risk_level TEXT,
                status TEXT DEFAULT 'open',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (provider_id) REFERENCES providers(id)
            )
        """)
        
        # Validation Status table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validation_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT DEFAULT 'idle',
                last_run_time TIMESTAMP,
                last_completion_time TIMESTAMP,
                total_providers INTEGER DEFAULT 0,
                validated_count INTEGER DEFAULT 0,
                needs_review_count INTEGER DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                provider_id INTEGER,
                agent_name TEXT,
                message TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (provider_id) REFERENCES providers(id)
            )
        """)
        
        conn.commit()


def insert_provider(provider_data: Dict[str, Any]) -> int:
    """
    Insert a new provider into the database.
    
    Args:
        provider_data: Dictionary containing provider information
        
    Returns:
        ID of the inserted provider
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Prepare data
        raw_data = json.dumps(provider_data.get('raw_data', {}))
        validated_data = json.dumps(provider_data.get('validated_data', {}))
        enriched_data = json.dumps(provider_data.get('enriched_data', {}))
        
        cursor.execute("""
            INSERT INTO providers (
                npi, first_name, last_name, organization_name, provider_type,
                specialty, address_line1, address_line2, city, state, zip_code,
                phone, email, website, license_number, license_state,
                practice_name, confidence_score, risk_score, validation_status,
                source_file, raw_data, validated_data, enriched_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            provider_data.get('npi'),
            provider_data.get('first_name'),
            provider_data.get('last_name'),
            provider_data.get('organization_name'),
            provider_data.get('provider_type'),
            provider_data.get('specialty'),
            provider_data.get('address_line1'),
            provider_data.get('address_line2'),
            provider_data.get('city'),
            provider_data.get('state'),
            provider_data.get('zip_code'),
            provider_data.get('phone'),
            provider_data.get('email'),
            provider_data.get('website'),
            provider_data.get('license_number'),
            provider_data.get('license_state'),
            provider_data.get('practice_name'),
            provider_data.get('confidence_score', 0),
            provider_data.get('risk_score', 0),
            provider_data.get('validation_status', 'pending'),
            provider_data.get('source_file'),
            raw_data,
            validated_data,
            enriched_data
        ))
        
        return cursor.lastrowid


def update_provider(provider_id: int, updates: Dict[str, Any]) -> bool:
    """
    Update an existing provider.
    
    Args:
        provider_id: ID of the provider to update
        updates: Dictionary containing fields to update
        
    Returns:
        True if update was successful
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Build update query dynamically
        update_fields = []
        values = []
        
        for key, value in updates.items():
            if key in ['raw_data', 'validated_data', 'enriched_data']:
                value = json.dumps(value) if isinstance(value, dict) else value
            update_fields.append(f"{key} = ?")
            values.append(value)
        
        # Always update updated_at
        update_fields.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(provider_id)
        
        query = f"UPDATE providers SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
        
        return cursor.rowcount > 0


def update_provider_after_validation(provider_id: int, updated_dict: Dict[str, Any]) -> bool:
    from datetime import datetime
    import json

    with get_db_connection() as conn:
        cursor = conn.cursor()

        update_fields = []
        values = []

        for key, value in updated_dict.items():
            # Serialize JSON fields properly
            if key in ["validated_data", "enriched_data", "raw_data"]:
                value = json.dumps(value)

            update_fields.append(f"{key} = ?")
            values.append(value)

        update_fields.append("updated_at = ?")
        values.append(datetime.now().isoformat())

        values.append(provider_id)

        query = f"""
            UPDATE providers
            SET {", ".join(update_fields)}
            WHERE id = ?
        """

        cursor.execute(query, values)
        conn.commit()

        return cursor.rowcount > 0



def insert_discrepancy(discrepancy_data: Dict[str, Any]) -> int:
    """
    Insert a discrepancy record.
    
    Args:
        discrepancy_data: Dictionary containing discrepancy information
        
    Returns:
        ID of the inserted discrepancy
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO discrepancies (
                provider_id, field_name, csv_value, api_value,
                scraped_value, final_value, confidence, risk_level,
                status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            discrepancy_data.get('provider_id'),
            discrepancy_data.get('field_name'),
            discrepancy_data.get('csv_value'),
            discrepancy_data.get('api_value'),
            discrepancy_data.get('scraped_value'),
            discrepancy_data.get('final_value'),
            discrepancy_data.get('confidence', 0),
            discrepancy_data.get('risk_level', 'medium'),
            discrepancy_data.get('status', 'open'),
            discrepancy_data.get('notes')
        ))
        conn.commit()
        
        return cursor.lastrowid


def insert_discrepancy_simple(provider_id: int, field: str, old_value: str, new_value: str) -> int:
    """
    Insert a simple discrepancy record.
    
    Args:
        provider_id: ID of the provider
        field: Field name that has discrepancy
        old_value: Old value (from CSV)
        new_value: New value (from API/scraped)
        
    Returns:
        ID of the inserted discrepancy
    """
    return insert_discrepancy({
        'provider_id': provider_id,
        'field_name': field,
        'csv_value': old_value,
        'api_value': new_value,
        'scraped_value': None,
        'final_value': new_value,
        'confidence': 80,
        'risk_level': 'medium',
        'status': 'open',
        'notes': f'Discrepancy found in {field}'
    })


def log_event(event_type: str, message: str, agent_name: Optional[str] = None,
              provider_id: Optional[int] = None, metadata: Optional[Dict] = None):
    """
    Log an event to the logs table.
    
    Args:
        event_type: Type of event (e.g., 'validation', 'enrichment', 'error')
        message: Log message
        agent_name: Name of the agent that generated the log
        provider_id: Optional provider ID
        metadata: Optional metadata dictionary
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute("""
            INSERT INTO logs (event_type, provider_id, agent_name, message, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (event_type, provider_id, agent_name, message, metadata_json))


def get_provider(provider_id: int) -> Optional[Dict[str, Any]]:
    """Get a provider by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM providers WHERE id = ?", (provider_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def get_provider_by_npi(npi: str) -> Optional[Dict[str, Any]]:
    """Get a provider by NPI."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM providers WHERE npi = ?", (npi,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def get_all_providers(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get all providers with pagination.
    
    Args:
        limit: Maximum number of providers to return
        offset: Number of providers to skip
        
    Returns:
        List of provider dictionaries
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM providers ORDER BY created_at DESC LIMIT ? OFFSET ?", 
                      (limit, offset))
        rows = cursor.fetchall()
        result = []
        for row in rows:
            provider_dict = dict(row)
            # Parse JSON fields
            if provider_dict.get('raw_data'):
                try:
                    provider_dict['raw_data'] = json.loads(provider_dict['raw_data'])
                except:
                    pass
            if provider_dict.get('validated_data'):
                try:
                    provider_dict['validated_data'] = json.loads(provider_dict['validated_data'])
                except:
                    pass
            if provider_dict.get('enriched_data'):
                try:
                    provider_dict['enriched_data'] = json.loads(provider_dict['enriched_data'])
                except:
                    pass
            result.append(provider_dict)
        return result


def get_discrepancies(provider_id: Optional[int] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get discrepancies, optionally filtered by provider_id or status."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM discrepancies WHERE 1=1"
        params = []
        
        if provider_id:
            query += " AND provider_id = ?"
            params.append(provider_id)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def get_validation_status() -> Dict[str, Any]:
    """
    Get current validation status.
    
    Returns:
        {
            "status": "idle|running|completed",
            "last_run_time": timestamp,
            "last_completion_time": timestamp,
            "total_providers": int,
            "validated_count": int,
            "needs_review_count": int,
            "error_message": str or None
        }
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM validation_status ORDER BY created_at DESC LIMIT 1")
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        else:
            # Initialize if doesn't exist
            cursor.execute("""
                INSERT INTO validation_status 
                (status, last_run_time, last_completion_time) 
                VALUES ('idle', NULL, NULL)
            """)
            conn.commit()
            return {
                "status": "idle",
                "last_run_time": None,
                "last_completion_time": None,
                "total_providers": 0,
                "validated_count": 0,
                "needs_review_count": 0,
                "error_message": None
            }


def set_validation_status_running() -> None:
    """Set validation status to running."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE validation_status 
            SET status = 'running', 
                last_run_time = CURRENT_TIMESTAMP,
                error_message = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = (SELECT MAX(id) FROM validation_status)
        """)
        conn.commit()


def set_validation_status_completed(validated_count: int, needs_review_count: int, 
                                   total_providers: int = 0, error_message: Optional[str] = None) -> None:
    """Set validation status to completed."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE validation_status 
            SET status = 'completed', 
                last_completion_time = CURRENT_TIMESTAMP,
                total_providers = ?,
                validated_count = ?,
                needs_review_count = ?,
                error_message = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = (SELECT MAX(id) FROM validation_status)
        """, (total_providers, validated_count, needs_review_count, error_message))
        conn.commit()


def set_validation_status_failed(error_message: str) -> None:
    """Set validation status to failed with error message."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE validation_status 
            SET status = 'failed', 
                error_message = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = (SELECT MAX(id) FROM validation_status)
        """, (error_message,))
        conn.commit()


# Initialize database on import
init_database()

