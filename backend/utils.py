"""
Utility functions for MedAtlas.
"""

import re
import phonenumbers
from typing import Optional, Dict, Any
from phonenumbers import geocoder, carrier


def validate_phone(phone: str, country_code: str = "US") -> Dict[str, Any]:
    """
    Validate phone number using phonenumbers library.
    
    Args:
        phone: Phone number string
        country_code: Country code (default: US)
        
    Returns:
        Dictionary with validation results
    """
    try:
        parsed = phonenumbers.parse(phone, country_code)
        is_valid = phonenumbers.is_valid_number(parsed)
        formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        
        return {
            "valid": is_valid,
            "formatted": formatted,
            "country": geocoder.description_for_number(parsed, "en"),
            "carrier": carrier.name_for_number(parsed, "en") if is_valid else None
        }
    except Exception as e:
        return {
            "valid": False,
            "formatted": None,
            "error": str(e)
        }


def normalize_address(address: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize address components.
    
    Args:
        address: Dictionary with address components
        
    Returns:
        Normalized address dictionary
    """
    normalized = {}
    
    # Normalize street address
    if address.get('address_line1'):
        normalized['address_line1'] = address['address_line1'].strip().title()
    
    if address.get('address_line2'):
        normalized['address_line2'] = address['address_line2'].strip().title()
    
    # Normalize city
    if address.get('city'):
        normalized['city'] = address['city'].strip().title()
    
    # Normalize state (uppercase, 2-letter code)
    if address.get('state'):
        state = address['state'].strip().upper()
        if len(state) > 2:
            # Convert full state name to abbreviation if needed
            state_abbrev = {
                'CALIFORNIA': 'CA', 'TEXAS': 'TX', 'FLORIDA': 'FL',
                'NEW YORK': 'NY', 'ILLINOIS': 'IL', 'PENNSYLVANIA': 'PA',
                'OHIO': 'OH', 'GEORGIA': 'GA', 'NORTH CAROLINA': 'NC',
                'MICHIGAN': 'MI'
            }
            normalized['state'] = state_abbrev.get(state, state[:2])
        else:
            normalized['state'] = state
    
    # Normalize ZIP code
    if address.get('zip_code'):
        zip_code = re.sub(r'[^\d]', '', str(address['zip_code']))
        if len(zip_code) == 9:
            normalized['zip_code'] = f"{zip_code[:5]}-{zip_code[5:]}"
        else:
            normalized['zip_code'] = zip_code[:5]
    
    return normalized


def normalize_specialty(specialty: str) -> str:
    """
    Normalize medical specialty names.
    
    Args:
        specialty: Specialty string
        
    Returns:
        Normalized specialty string
    """
    if not specialty:
        return ""
    
    specialty = specialty.strip().title()
    
    # Common specialty mappings
    mappings = {
        "Internal Medicine": "Internal Medicine",
        "Family Practice": "Family Medicine",
        "Family Med": "Family Medicine",
        "Cardiology": "Cardiology",
        "Orthopedics": "Orthopedic Surgery",
        "Ortho": "Orthopedic Surgery",
        "Pediatrics": "Pediatrics",
        "Peds": "Pediatrics",
        "Dermatology": "Dermatology",
        "Derm": "Dermatology",
        "Psychiatry": "Psychiatry",
        "Psych": "Psychiatry",
        "Ob/Gyn": "Obstetrics and Gynecology",
        "OBGYN": "Obstetrics and Gynecology",
        "Emergency Medicine": "Emergency Medicine",
        "ER": "Emergency Medicine",
        "General Surgery": "General Surgery",
        "Surgery": "General Surgery"
    }
    
    return mappings.get(specialty, specialty)


def calculate_confidence_score(provider_data: Dict[str, Any], 
                               validation_results: Dict[str, Any]) -> int:
    """
    Calculate confidence score (0-100) based on validation results.
    
    Args:
        provider_data: Provider data dictionary
        validation_results: Validation results dictionary
        
    Returns:
        Confidence score (0-100)
    """
    score = 0
    max_score = 0
    
    # NPI validation (20 points)
    max_score += 20
    if validation_results.get('npi_valid'):
        score += 20
    elif provider_data.get('npi'):
        score += 10  # Partial credit if NPI exists but not validated
    
    # Address validation (20 points)
    max_score += 20
    if validation_results.get('address_valid'):
        score += 20
    elif provider_data.get('address_line1') and provider_data.get('city'):
        score += 10
    
    # Phone validation (15 points)
    max_score += 15
    if validation_results.get('phone_valid'):
        score += 15
    elif provider_data.get('phone'):
        score += 7
    
    # License validation (15 points)
    max_score += 15
    if validation_results.get('license_valid'):
        score += 15
    elif provider_data.get('license_number'):
        score += 7
    
    # Website validation (10 points)
    max_score += 10
    if validation_results.get('website_valid'):
        score += 10
    elif provider_data.get('website'):
        score += 5
    
    # Data completeness (20 points)
    max_score += 20
    required_fields = ['npi', 'first_name', 'last_name', 'address_line1', 
                      'city', 'state', 'zip_code', 'phone']
    present_fields = sum(1 for field in required_fields if provider_data.get(field))
    score += int((present_fields / len(required_fields)) * 20)
    
    return min(100, int((score / max_score) * 100))


def calculate_risk_score(discrepancies: list, confidence_score: int) -> int:
    """
    Calculate risk score (0-100) based on discrepancies and confidence.
    
    Args:
        discrepancies: List of discrepancy dictionaries
        confidence_score: Current confidence score
        
    Returns:
        Risk score (0-100)
    """
    risk = 0
    
    # Base risk from low confidence
    if confidence_score < 50:
        risk += 40
    elif confidence_score < 70:
        risk += 20
    
    # Risk from discrepancies
    high_risk_fields = ['npi', 'license_number', 'address_line1', 'phone']
    for disc in discrepancies:
        if disc.get('field_name') in high_risk_fields:
            risk += 15
        else:
            risk += 5
    
    return min(100, risk)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + '.' + ext
    
    return filename

