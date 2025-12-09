"""
Pydantic models for MedAtlas API.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class ProviderBase(BaseModel):
    """Base provider model."""
    npi: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization_name: Optional[str] = None
    provider_type: Optional[str] = None
    specialty: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    license_number: Optional[str] = None
    license_state: Optional[str] = None
    practice_name: Optional[str] = None


class ProviderCreate(ProviderBase):
    """Model for creating a provider."""
    source_file: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class Provider(ProviderBase):
    """Full provider model with all fields."""
    id: int
    confidence_score: int = Field(default=0, ge=0, le=100)
    risk_score: int = Field(default=0, ge=0, le=100)
    validation_status: str = "pending"
    source_file: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    raw_data: Optional[Dict[str, Any]] = None
    validated_data: Optional[Dict[str, Any]] = None
    enriched_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class DiscrepancyBase(BaseModel):
    """Base discrepancy model."""
    provider_id: int
    field_name: str
    csv_value: Optional[str] = None
    api_value: Optional[str] = None
    scraped_value: Optional[str] = None
    final_value: Optional[str] = None
    confidence: int = Field(default=0, ge=0, le=100)
    risk_level: str = "medium"
    status: str = "open"
    notes: Optional[str] = None


class DiscrepancyCreate(DiscrepancyBase):
    """Model for creating a discrepancy."""
    pass


class Discrepancy(DiscrepancyBase):
    """Full discrepancy model."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ValidationRequest(BaseModel):
    """Request model for validation endpoint."""
    provider_id: Optional[int] = None
    npi: Optional[str] = None
    force_revalidate: bool = False


class ValidationResult(BaseModel):
    """Result model for validation."""
    provider_id: int
    validated: bool
    confidence_score: int
    discrepancies: List[Discrepancy]
    validated_data: Dict[str, Any]


class UploadResponse(BaseModel):
    """Response model for file upload."""
    success: bool
    message: str
    provider_count: Optional[int] = None
    file_id: Optional[str] = None


class ExportRequest(BaseModel):
    """Request model for export endpoint."""
    format: str = Field(default="csv", pattern="^(csv|json)$")
    provider_ids: Optional[List[int]] = None
    include_discrepancies: bool = True


class SummaryStats(BaseModel):
    """Summary statistics model."""
    total_providers: int
    validated_providers: int
    pending_providers: int
    total_discrepancies: int
    open_discrepancies: int
    avg_confidence_score: float
    high_risk_providers: int

