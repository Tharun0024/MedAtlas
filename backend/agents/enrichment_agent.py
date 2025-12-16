# """
# Enrichment Agent for MedAtlas.

# Responsibilities:
# - Extract additional provider data from PDFs using OCR (pytesseract).
# - Simulate license registry validation with safe defaults.
# - Normalize fields (phone, names, addresses, specialties).
# - Combine results into a single enriched_data payload.

# Design goals:
# - Lightweight and resilient for prototype use.
# - Never crash on missing files or OCR/API failures.
# - Clear, modular functions that can be swapped with real services later.
# """

# import logging
# import os
# import re
# from typing import Dict, Any, Optional

# try:
#     import pytesseract
# except Exception:  # pragma: no cover - safe fallback if not available
#     pytesseract = None

# try:
#     from pdf2image import convert_from_path
# except Exception:  # pragma: no cover
#     convert_from_path = None

# from backend.utils import normalize_specialty, normalize_address
# from backend.database import log_event

# logger = logging.getLogger(__name__)


# class EnrichmentAgent:
#     """Agent responsible for enriching provider data."""

#     def __init__(self):
#         self.name = "EnrichmentAgent"

#     async def run(self, provider_data: Dict[str, Any], pdf_path: Optional[str] = None) -> Dict[str, Any]:
#         """
#         Entry point for enrichment.

#         Args:
#             provider_data: Provider record
#             pdf_path: Optional path to PDF for OCR extraction

#         Returns:
#             enriched_data dict with merged/enhanced fields
#         """
#         provider_id = provider_data.get("id")
#         log_event("enrichment_start", f"Starting enrichment for provider {provider_data.get('npi')}", self.name, provider_id)

#         enriched_data = provider_data.copy()

#         # 1) PDF OCR enrichment
#         if pdf_path and os.path.exists(pdf_path):
#             pdf_result = await self.enrich_from_pdf(pdf_path)
#             for key, val in pdf_result.get("structured_data", {}).items():
#                 if val and not enriched_data.get(key):
#                     enriched_data[key] = val

#         # 2) License registry (simulated)
#         license_result = await self.enrich_from_license_registry(enriched_data)
#         enriched_data.update(license_result)

#         # 3) Normalize fields
#         enriched_data = await self.normalize_fields(enriched_data)

#         log_event("enrichment_complete", f"Enrichment complete for provider {provider_data.get('npi')}", self.name, provider_id)
#         return enriched_data

#     async def enrich_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
#         """
#         Use pytesseract to extract text from PDF pages and pull key fields.
#         Safe fallbacks if OCR is unavailable or fails.
#         """
#         structured: Dict[str, Any] = {}

#         if not pytesseract or not convert_from_path:
#             logger.warning("OCR dependencies not available; skipping PDF enrichment.")
#             return {"success": False, "structured_data": structured}

#         try:
#             images = convert_from_path(pdf_path, dpi=200)
#             full_text_parts = []
#             for img in images:
#                 try:
#                     text = pytesseract.image_to_string(img)
#                 except Exception:
#                     text = ""
#                 if text:
#                     full_text_parts.append(text)
#             full_text = "\n".join(full_text_parts)

#             # Extract license number
#             license_patterns = [
#                 r"License[:\\s#]+([A-Z0-9-]+)",
#                 r"Lic\\.\\s*#?\\s*([A-Z0-9-]+)",
#                 r"License\\s+Number[:\\s]+([A-Z0-9-]+)",
#                 r"MD\\s*License[:\\s]+([A-Z0-9-]+)",
#             ]
#             for pattern in license_patterns:
#                 match = re.search(pattern, full_text, re.IGNORECASE)
#                 if match:
#                     structured["license_number"] = match.group(1).strip()
#                     break

#             # Extract provider name (first + last)
#             name_patterns = [
#                 r"Dr\\.\\s+([A-Z][a-zA-Z]+\\s+[A-Z][a-zA-Z]+)",
#                 r"Provider[:\\s]+([A-Z][a-zA-Z]+\\s+[A-Z][a-zA-Z]+)",
#                 r"([A-Z][a-zA-Z]+\\s+[A-Z][a-zA-Z]+),\\s*M\\.D\\.",
#             ]
#             for pattern in name_patterns:
#                 match = re.search(pattern, full_text)
#                 if match:
#                     parts = match.group(1).split()
#                     if len(parts) >= 2:
#                         structured["first_name"] = parts[0].strip()
#                         structured["last_name"] = " ".join(parts[1:]).strip()
#                     break

#             # Extract specialty keywords
#             specialty_keywords = [
#                 "cardiology",
#                 "orthopedic",
#                 "pediatric",
#                 "dermatology",
#                 "family medicine",
#                 "internal medicine",
#                 "psychiatry",
#                 "obstetrics",
#                 "gynecology",
#             ]
#             lower_text = full_text.lower()
#             for kw in specialty_keywords:
#                 if kw in lower_text:
#                     structured["specialty"] = kw.title()
#                     break

#             return {"success": True, "structured_data": structured}
#         except Exception as e:
#             logger.error(f"OCR extraction failed: {e}")
#             return {"success": False, "structured_data": structured}

#     async def enrich_from_license_registry(self, provider: Dict[str, Any]) -> Dict[str, Any]:
#         """
#         Simulate a license registry lookup. Returns active if license_number present, else unknown.
#         """
#         license_number = provider.get("license_number")
#         license_state = provider.get("license_state")

#         if license_number:
#             return {
#                 "license_status": "active",
#                 "license_verified": True,
#                 "license_state": license_state,
#             }

#         return {
#             "license_status": "unknown",
#             "license_verified": False,
#             "license_state": license_state,
#         }

#     async def normalize_fields(self, provider: Dict[str, Any]) -> Dict[str, Any]:
#         """
#         Normalize phone, names, addresses, and specialties.
#         """
#         normalized = provider.copy()

#         # Phone normalization: keep digits, format if US-length
#         phone = normalized.get("phone")
#         if phone:
#             digits = re.sub(r"\\D", "", phone)
#             if len(digits) == 10:
#                 normalized["phone"] = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
#             elif len(digits) == 11 and digits.startswith("1"):
#                 digits = digits[1:]
#                 if len(digits) == 10:
#                     normalized["phone"] = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"

#         # Trim whitespace in names
#         for field in ["first_name", "last_name", "organization_name", "practice_name"]:
#             if normalized.get(field):
#                 normalized[field] = str(normalized[field]).strip()

#         # Normalize address
#         address_input = {
#             "address_line1": normalized.get("address_line1"),
#             "address_line2": normalized.get("address_line2"),
#             "city": normalized.get("city"),
#             "state": normalized.get("state"),
#             "zip_code": normalized.get("zip_code"),
#         }
#         normalized.update(normalize_address(address_input))

#         # Normalize specialty
#         if normalized.get("specialty"):
#             normalized["specialty"] = normalize_specialty(normalized["specialty"])

#         return normalized
# """
# Enrichment Agent for MedAtlas.
# Enriches provider data from PDFs, websites, and directories.
# """

# import logging
# import os
# from typing import Dict, Any, Optional
# from backend.ocr import extract_text_from_pdf, parse_provider_data
# from backend.scraping import scrape_provider_website, verify_license
# from backend.utils import normalize_specialty, normalize_address, validate_phone
# from backend.database import log_event

# logger = logging.getLogger(__name__)


# class EnrichmentAgent:
#     """Agent responsible for enriching provider data."""
    
#     def __init__(self):
#         self.name = "EnrichmentAgent"
    
#     async def enrich_provider(self, provider_data: Dict[str, Any], 
#                              pdf_path: Optional[str] = None) -> Dict[str, Any]:
#         """
#         Enrich provider data from multiple sources.
        
#         Args:
#             provider_data: Provider data dictionary
#             pdf_path: Optional path to PDF file for OCR extraction
            
#         Returns:
#             Dictionary with enriched data
#         """
#         log_event("enrichment_start", 
#                  f"Starting enrichment for provider {provider_data.get('npi')}", 
#                  self.name, provider_data.get('id'))
        
#         enriched_data = provider_data.copy()
        
#         # Extract data from PDF if provided
#         if pdf_path and os.path.exists(pdf_path):
#             pdf_data = await self.enrich_from_pdf(pdf_path)
#             if pdf_data.get("success"):
#                 pdf_structured = pdf_data.get("structured_data", {})
#                 for key, value in pdf_structured.items():
#                     if value and not enriched_data.get(key):
#                         enriched_data[key] = value
#                         log_event("enrichment", f"Added {key} from PDF", self.name, provider_data.get('id'))
        
#         # Enrich from provider website
#         if provider_data.get('website'):
#             website_data = await scrape_provider_website(provider_data['website'])
#             if website_data.get("success") and website_data.get("data"):
#                 website_info = website_data["data"]
#                 for key, value in website_info.items():
#                     if value and not enriched_data.get(key):
#                         enriched_data[key] = value
#                         log_event("enrichment", f"Added {key} from website", self.name, provider_data.get('id'))
        
#         # Check state license status
#         if provider_data.get('license_number') and provider_data.get('license_state'):
#             license_result = await self.enrich_from_state_license(provider_data)
#             if license_result.get("verified"):
#                 enriched_data["license_status"] = license_result.get("status", "active")
#                 enriched_data["license_verified"] = True
#                 enriched_data["license_expiry"] = license_result.get("expiry_date")
        
#         # Normalize all fields
#         enriched_data = await self.normalize_fields(enriched_data)
        
#         log_event("enrichment_complete", 
#                  f"Enrichment complete for provider {provider_data.get('npi')}", 
#                  self.name, provider_data.get('id'))
        
#         return enriched_data
    
#     async def enrich_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
#         """
#         Extract provider data from PDF using Tesseract OCR.
#         Extract license number, provider name, clinic name.
        
#         Args:
#             pdf_path: Path to PDF file
            
#         Returns:
#             Dictionary with extracted structured data
#         """
#         try:
#             result = extract_text_from_pdf(pdf_path)
            
#             if result.get("success"):
#                 structured_data = result.get("structured_data", {})
                
#                 # Additional parsing for specific fields
#                 full_text = result.get("full_text", "")
                
#                 # Extract license number with better patterns
#                 if not structured_data.get("license_number"):
#                     license_patterns = [
#                         r'License[:\s#]+([A-Z0-9-]+)',
#                         r'Lic\.\s*#?\s*([A-Z0-9-]+)',
#                         r'License\s+Number[:\s]+([A-Z0-9-]+)',
#                         r'MD\s*License[:\s]+([A-Z0-9-]+)'
#                     ]
#                     for pattern in license_patterns:
#                         import re
#                         matches = re.findall(pattern, full_text, re.IGNORECASE)
#                         if matches:
#                             structured_data["license_number"] = matches[0]
#                             break
                
#                 # Extract provider name
#                 if not structured_data.get("name"):
#                     name_patterns = [
#                         r'Dr\.\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
#                         r'([A-Z][a-z]+\s+[A-Z][a-z]+),\s*M\.D\.',
#                         r'([A-Z][a-z]+\s+[A-Z][a-z]+),\s*DO',
#                         r'Provider[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)'
#                     ]
#                     for pattern in name_patterns:
#                         import re
#                         matches = re.findall(pattern, full_text)
#                         if matches:
#                             name_parts = matches[0].split()
#                             if len(name_parts) >= 2:
#                                 structured_data["first_name"] = name_parts[0]
#                                 structured_data["last_name"] = " ".join(name_parts[1:])
#                             break
                
#                 # Extract clinic/practice name
#                 if not structured_data.get("practice_name"):
#                     clinic_patterns = [
#                         r'Practice[:\s]+([A-Z][a-zA-Z\s&]+)',
#                         r'Clinic[:\s]+([A-Z][a-zA-Z\s&]+)',
#                         r'Medical\s+Group[:\s]+([A-Z][a-zA-Z\s&]+)'
#                     ]
#                     for pattern in clinic_patterns:
#                         import re
#                         matches = re.findall(pattern, full_text)
#                         if matches:
#                             structured_data["practice_name"] = matches[0].strip()
#                             break
                
#                 return {
#                     "success": True,
#                     "structured_data": structured_data,
#                     "text_length": len(full_text)
#                 }
#             else:
#                 return {
#                     "success": False,
#                     "error": result.get("error", "Failed to extract PDF"),
#                     "structured_data": {}
#                 }
#         except Exception as e:
#             logger.error(f"Error extracting from PDF: {e}")
#             return {
#                 "success": False,
#                 "error": str(e),
#                 "structured_data": {}
#             }
    
#     async def enrich_from_state_license(self, provider: Dict[str, Any]) -> Dict[str, Any]:
#         """
#         Scrape state medical board to validate license.
#         Check expiration date.
        
#         Args:
#             provider: Provider data dictionary
            
#         Returns:
#             Dictionary with license validation results
#         """
#         try:
#             license_number = provider.get('license_number')
#             license_state = provider.get('license_state')
#             provider_name = f"{provider.get('first_name', '')} {provider.get('last_name', '')}".strip()
            
#             if not license_number or not license_state:
#                 return {
#                     "verified": False,
#                     "error": "Missing license number or state"
#                 }
            
#             # Use license scraper
#             result = await verify_license(license_number, license_state, provider_name)
            
#             return result
#         except Exception as e:
#             logger.error(f"Error validating license: {e}")
#             return {
#                 "verified": False,
#                 "error": str(e),
#                 "status": "unknown"
#             }
    
#     async def normalize_fields(self, provider: Dict[str, Any]) -> Dict[str, Any]:
#         """
#         Normalize specialty, phone, address, license formats.
        
#         Args:
#             provider: Provider data dictionary
            
#         Returns:
#             Normalized provider data
#         """
#         normalized = provider.copy()
        
#         # Normalize specialty
#         if normalized.get('specialty'):
#             normalized['specialty'] = normalize_specialty(normalized['specialty'])
        
#         # Normalize phone
#         if normalized.get('phone'):
#             phone_result = validate_phone(normalized['phone'])
#             if phone_result.get("formatted"):
#                 normalized['phone'] = phone_result["formatted"]
        
#         # Normalize address
#         address_fields = {
#             "address_line1": normalized.get("address_line1"),
#             "address_line2": normalized.get("address_line2"),
#             "city": normalized.get("city"),
#             "state": normalized.get("state"),
#             "zip_code": normalized.get("zip_code")
#         }
#         normalized_addr = normalize_address(address_fields)
#         normalized.update(normalized_addr)
        
#         # Normalize license number (remove spaces, standardize format)
#         if normalized.get('license_number'):
#             license = normalized['license_number'].strip().upper()
#             # Remove common separators and keep alphanumeric
#             import re
#             license = re.sub(r'[^A-Z0-9]', '', license)
#             normalized['license_number'] = license
        
#         # Normalize state codes
#         if normalized.get('state'):
#             state = normalized['state'].strip().upper()
#             if len(state) > 2:
#                 # Convert full state name to abbreviation
#                 state_map = {
#                     'CALIFORNIA': 'CA', 'TEXAS': 'TX', 'FLORIDA': 'FL',
#                     'NEW YORK': 'NY', 'ILLINOIS': 'IL', 'PENNSYLVANIA': 'PA',
#                     'OHIO': 'OH', 'GEORGIA': 'GA', 'NORTH CAROLINA': 'NC',
#                     'MICHIGAN': 'MI', 'NEW JERSEY': 'NJ', 'VIRGINIA': 'VA',
#                     'WASHINGTON': 'WA', 'MASSACHUSETTS': 'MA', 'ARIZONA': 'AZ'
#                 }
#                 normalized['state'] = state_map.get(state, state[:2])
#             else:
#                 normalized['state'] = state
        
#         return normalized
    
#     async def enrich_from_hospital_directories(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
#         """
#         Enrich provider data from hospital directories.
        
#         Note: This is a placeholder for future implementation.
        
#         Args:
#             provider_data: Provider data dictionary
            
#         Returns:
#             Enriched provider data
#         """
#         # Placeholder - would integrate with hospital directory APIs
#         return provider_data


import logging
from typing import Dict, Any, Optional

from backend.database import log_event

logger = logging.getLogger(__name__)


class EnrichmentAgent:
    def __init__(self):
        self.name = "EnrichmentAgent"

    async def enrich_provider(
        self,
        validated_data: Dict[str, Any],
        pdf_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Enrich a validated provider record.

        Args:
            validated_data: Provider data after DataValidationAgent.
            pdf_path: Optional path to a PDF for OCR/document checks.

        Returns:
            Enriched provider data (dict).
        """
        provider_id = validated_data.get("id")
        npi = validated_data.get("npi")

        log_event(
            "enrichment_start",
            f"Starting enrichment for provider {npi}",
            self.name,
            provider_id,
        )

        # TODO: plug in real enrichment logic, using pdf_path + OCR if needed.
        # For now, keep minimal safe behavior: no extra fields, just echo validated_data.
        enriched_data: Dict[str, Any] = dict(validated_data)

        log_event(
            "enrichment_complete",
            f"Enrichment complete for provider {npi}",
            self.name,
            provider_id,
        )

        return enriched_data
