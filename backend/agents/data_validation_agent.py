"""
Data Validation Agent for MedAtlas.
Performs lightweight, real validation against phone, address, NPI registry,
and website scraping. Designed for prototype use with graceful fallbacks.
"""

import re
import logging
from typing import Dict, Any, Optional

import aiohttp
from bs4 import BeautifulSoup

from backend.utils import normalize_address
from backend.database import log_event

logger = logging.getLogger(__name__)

NPI_REGISTRY_URL = "https://npiregistry.cms.hhs.gov/api/"


class DataValidationAgent:
    """Agent responsible for validating provider data."""

    def __init__(self):
        self.name = "DataValidationAgent"

    async def run(self, provider: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run validation on a provider and return validated data with confidence scores.

        Returns:
            {
                "validated_data": {...},
                "confidence_scores": {...}
            }
        """
        provider_id = provider.get("id")
        log_event("validation_start", f"Starting validation for provider {provider.get('npi')}", self.name, provider_id)

        validated_data = provider.copy()
        confidence_scores: Dict[str, int] = {}

        # Phone
        phone_result = await self.validate_phone(provider.get("phone"))
        confidence_scores["phone"] = phone_result["confidence"]
        if phone_result["formatted"]:
            validated_data["phone"] = phone_result["formatted"]

        # Address
        address_result = await self.validate_address(
            provider.get("address_line1"),
            provider.get("city"),
            provider.get("state"),
            provider.get("zip_code"),
        )
        confidence_scores["address"] = address_result["confidence"]
        if address_result["normalized_address"]:
            validated_data.update(address_result["normalized_address"])

        # NPI
        npi_result = await self.validate_npi(provider.get("npi"), provider)
        confidence_scores["npi"] = npi_result["confidence"]
        if npi_result["data"]:
            for key, value in npi_result["data"].items():
                if value and not validated_data.get(key):
                    validated_data[key] = value

        # Website
        website_result = await self.scrape_website(provider.get("website"))
        confidence_scores["website"] = website_result["confidence"]
        if website_result["data"]:
            for key, value in website_result["data"].items():
                if value and not validated_data.get(key):
                    validated_data[key] = value

        log_event(
            "validation_complete",
            f"Validation complete for provider {provider.get('npi')}",
            self.name,
            provider_id,
        )

        return {
            "validated_data": validated_data,
            "confidence_scores": confidence_scores,
        }

    async def validate_phone(self, phone: Optional[str]) -> Dict[str, Any]:
        """Validate phone format using regex and normalize."""
        if not phone:
            return {"valid": False, "formatted": None, "confidence": 0}

        try:
            digits = re.sub(r"\\D", "", phone)
            confidence = 0
            formatted = phone

            if len(digits) == 10:
                formatted = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
                confidence = 100
            elif len(digits) == 11 and digits.startswith("1"):
                digits = digits[1:]
                formatted = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
                confidence = 100
            elif len(digits) >= 7:
                confidence = 60

            return {"valid": confidence >= 60, "formatted": formatted, "confidence": confidence}
        except Exception as e:
            logger.error(f"validate_phone error: {e}")
            return {"valid": False, "formatted": phone, "confidence": 0}

    async def validate_address(
        self, address_line1: Optional[str], city: Optional[str], state: Optional[str], zip_code: Optional[str]
    ) -> Dict[str, Any]:
        """
        Lightweight address normalization with confidence scoring.
        No external API to keep prototype fast and resilient.
        """
        if not address_line1:
            return {"valid": False, "normalized_address": None, "confidence": 0}

        try:
            normalized_address = normalize_address(
                {
                    "address_line1": address_line1 or "",
                    "address_line2": "",
                    "city": city or "",
                    "state": state or "",
                    "zip_code": zip_code or "",
                }
            )

            # Confidence heuristic
            has_city_state = bool(city) and bool(state)
            confidence = 80 if has_city_state else 60 if address_line1 else 30

            return {
                "valid": confidence >= 60,
                "normalized_address": normalized_address,
                "confidence": confidence,
            }
        except Exception as e:
            logger.error(f"validate_address error: {e}")
            return {"valid": False, "normalized_address": None, "confidence": 0}

    async def validate_npi(self, npi: Optional[str], original: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate NPI using NPI Registry API.
        Returns extracted data and a confidence score.
        """
        if not npi:
            return {"valid": False, "data": {}, "confidence": 0}

        try:
            async with aiohttp.ClientSession() as session:
                params = {"number": npi, "version": "2.1"}
                async with session.get(NPI_REGISTRY_URL, params=params, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status != 200:
                        return {"valid": False, "data": {}, "confidence": 0}
                    payload = await resp.json()

            if payload.get("result_count", 0) == 0:
                return {"valid": False, "data": {}, "confidence": 0}

            result = payload.get("results", [])[0]
            data: Dict[str, Any] = {}

            basic = result.get("basic", {})
            data["first_name"] = basic.get("first_name")
            data["last_name"] = basic.get("last_name")
            data["organization_name"] = basic.get("organization_name")
            data["provider_type"] = basic.get("enumeration_type")

            addresses = result.get("addresses", [])
            if addresses:
                primary = addresses[0]
                data["address_line1"] = primary.get("address_1")
                data["address_line2"] = primary.get("address_2")
                data["city"] = primary.get("city")
                data["state"] = primary.get("state")
                data["zip_code"] = primary.get("postal_code")
                data["phone"] = primary.get("telephone_number")

            taxonomies = result.get("taxonomies", [])
            if taxonomies:
                data["specialty"] = taxonomies[0].get("desc")

            # Confidence based on field matches with original
            confidence = 80
            match_fields = ["first_name", "last_name", "city", "state"]
            matches = 0
            total = 0
            if original:
                for field in match_fields:
                    api_val = data.get(field)
                    orig_val = original.get(field)
                    if api_val:
                        total += 1
                        if orig_val and str(api_val).strip().lower() == str(orig_val).strip().lower():
                            matches += 1
            if total > 0:
                confidence = int(50 + 50 * (matches / total))

            return {"valid": True, "data": data, "confidence": confidence}
        except Exception as e:
            logger.error(f"validate_npi error: {e}")
            return {"valid": False, "data": {}, "confidence": 0}

    async def scrape_website(self, url: Optional[str]) -> Dict[str, Any]:
        """
        Scrape a website using aiohttp + BeautifulSoup.
        Extracts phone, specialty keywords, and practice/clinic name.
        """
        if not url or not url.startswith(("http://", "https://")):
            return {"valid": False, "data": {}, "confidence": 0}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status != 200:
                        return {"valid": False, "data": {}, "confidence": 0}
                    html = await resp.text()
        except Exception as e:
            logger.error(f"scrape_website fetch error: {e}")
            return {"valid": False, "data": {}, "confidence": 0}

        try:
            soup = BeautifulSoup(html, "html.parser")
            extracted: Dict[str, Any] = {}

            # Phone
            phone_matches = re.findall(r"\\(?\\d{3}\\)?[-.\\s]?\\d{3}[-.\\s]?\\d{4}", html)
            if phone_matches:
                extracted["phone"] = phone_matches[0]

            # Practice/clinic name
            title = soup.find("title")
            if title and title.text:
                extracted["practice_name"] = title.text.strip()[:120]
            if not extracted.get("practice_name"):
                h1 = soup.find("h1")
                if h1 and h1.text:
                    extracted["practice_name"] = h1.text.strip()[:120]

            # Specialty keywords
            specialty_keywords = [
                "cardiology",
                "orthopedic",
                "pediatric",
                "dermatology",
                "family",
                "internal medicine",
                "psychiatry",
            ]
            text_lower = soup.get_text(" ").lower()
            for kw in specialty_keywords:
                if kw in text_lower:
                    extracted["specialty"] = kw.title()
                    break

            # Confidence heuristic
            confidence = 0
            if extracted.get("phone"):
                confidence += 40
            if extracted.get("practice_name"):
                confidence += 30
            if extracted.get("specialty"):
                confidence += 30

            return {"valid": confidence >= 40, "data": extracted, "confidence": min(confidence, 100)}
        except Exception as e:
            logger.error(f"scrape_website parse error: {e}")
            return {"valid": False, "data": {}, "confidence": 0}
"""
Data Validation Agent for MedAtlas.
Validates provider data through API checks and web scraping.
"""

import aiohttp
import logging
import re
from typing import Dict, Any, Optional
from backend.utils import validate_phone, normalize_address
from backend.scraping import validate_address_google, verify_website_exists, scrape_provider_website
from backend.database import log_event

logger = logging.getLogger(__name__)

# NPI Registry API endpoint
NPI_REGISTRY_URL = "https://npiregistry.cms.hhs.gov/api/"


class DataValidationAgent:
    """Agent responsible for validating provider data."""
    
    def __init__(self):
        self.name = "DataValidationAgent"
    
    async def validate_provider(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate provider data through multiple sources.
        
        Args:
            provider_data: Provider data dictionary
            
        Returns:
            Dictionary with validation results and confidence scores
        """
        log_event("validation_start", f"Starting validation for provider {provider_data.get('npi')}", 
                 self.name, provider_data.get('id'))
        
        validation_results = {
            "npi_valid": False,
            "phone_valid": False,
            "address_valid": False,
            "website_valid": False,
            "validated_data": provider_data.copy(),
            "confidence_scores": {}
        }
        
        # Validate NPI
        if provider_data.get('npi'):
            npi_result = await self.validate_npi(provider_data['npi'], provider_data)
            validation_results["npi_valid"] = npi_result.get("valid", False)
            validation_results["confidence_scores"]["npi"] = npi_result.get("confidence", 0)
            
            if npi_result.get("valid") and npi_result.get("data"):
                # Update provider data with validated information
                npi_data = npi_result["data"]
                validation_results["validated_data"].update({
                    "first_name": npi_data.get("first_name") or provider_data.get("first_name"),
                    "last_name": npi_data.get("last_name") or provider_data.get("last_name"),
                    "organization_name": npi_data.get("organization_name") or provider_data.get("organization_name"),
                    "provider_type": npi_data.get("provider_type") or provider_data.get("provider_type"),
                    "address_line1": npi_data.get("address_line1") or provider_data.get("address_line1"),
                    "city": npi_data.get("city") or provider_data.get("city"),
                    "state": npi_data.get("state") or provider_data.get("state"),
                    "zip_code": npi_data.get("zip_code") or provider_data.get("zip_code"),
                    "phone": npi_data.get("phone") or provider_data.get("phone"),
                    "specialty": npi_data.get("specialty") or provider_data.get("specialty"),
                })
        
        # Validate phone
        if provider_data.get('phone'):
            phone_result = await self.validate_phone(provider_data['phone'])
            validation_results["phone_valid"] = phone_result.get("valid", False)
            validation_results["confidence_scores"]["phone"] = phone_result.get("confidence", 0)
            
            if phone_result.get("formatted"):
                validation_results["validated_data"]["phone"] = phone_result["formatted"]
        
        # Validate address via Google Places
        if provider_data.get('address_line1') and provider_data.get('city'):
            address_result = await self.validate_address(
                provider_data['address_line1'],
                provider_data.get('city', ''),
                provider_data.get('state', ''),
                provider_data.get('zip_code', '')
            )
            validation_results["address_valid"] = address_result.get("valid", False)
            validation_results["confidence_scores"]["address"] = address_result.get("confidence", 0)
            
            if address_result.get("normalized_address"):
                validation_results["validated_data"].update(address_result["normalized_address"])
        
        # Validate and scrape website
        if provider_data.get('website'):
            website_result = await self.scrape_website(provider_data['website'])
            validation_results["website_valid"] = website_result.get("valid", False)
            validation_results["confidence_scores"]["website"] = website_result.get("confidence", 0)
            
            if website_result.get("data"):
                # Merge website data
                for key, value in website_result["data"].items():
                    if value and not validation_results["validated_data"].get(key):
                        validation_results["validated_data"][key] = value
        
        log_event("validation_complete", 
                 f"Validation complete for provider {provider_data.get('npi')}", 
                 self.name, provider_data.get('id'))
        
        return validation_results
    
    async def validate_phone(self, phone: str) -> Dict[str, Any]:
        """
        Validate phone format using regex and return standardized number.
        
        Args:
            phone: Phone number string
            
        Returns:
            Dictionary with validation results, formatted number, and confidence
        """
        try:
            # Remove all non-digit characters
            digits_only = re.sub(r'\D', '', phone)
            
            # Check if it's a valid US phone number (10 or 11 digits)
            if len(digits_only) == 10:
                # Format as (XXX) XXX-XXXX
                formatted = f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
                confidence = 100
            elif len(digits_only) == 11 and digits_only[0] == '1':
                # Remove leading 1
                digits_only = digits_only[1:]
                formatted = f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
                confidence = 100
            else:
                formatted = phone
                confidence = 50 if len(digits_only) >= 7 else 0
            
            # Use phonenumbers library for additional validation
            phone_validation = validate_phone(phone)
            if phone_validation.get("valid"):
                confidence = 100
                formatted = phone_validation.get("formatted", formatted)
            
            return {
                "valid": confidence >= 80,
                "formatted": formatted,
                "confidence": confidence
            }
        except Exception as e:
            logger.error(f"Error validating phone {phone}: {e}")
            return {
                "valid": False,
                "formatted": phone,
                "confidence": 0,
                "error": str(e)
            }
    
    async def validate_address(self, address: str, city: str = "", state: str = "", zip_code: str = "") -> Dict[str, Any]:
        """
        Validate address using Google Places API.
        Extract formatted address, lat/lng, region/state.
        Confidence based on Google match quality.
        
        Args:
            address: Street address
            city: City name
            state: State code
            zip_code: ZIP code
            
        Returns:
            Dictionary with validation results and confidence
        """
        try:
            result = await validate_address_google(address, city, state, zip_code)
            
            if result.get("valid"):
                # Calculate confidence based on match quality
                confidence = 100  # High confidence if Google found exact match
                
                # Check if state matches
                if state and result.get("normalized_address", {}).get("state"):
                    if state.upper() != result["normalized_address"]["state"].upper():
                        confidence = 80  # Lower confidence if state mismatch
                
                return {
                    "valid": True,
                    "formatted_address": result.get("formatted_address"),
                    "latitude": result.get("latitude"),
                    "longitude": result.get("longitude"),
                    "normalized_address": result.get("normalized_address"),
                    "confidence": confidence
                }
            else:
                return {
                    "valid": False,
                    "confidence": 0,
                    "error": result.get("error", "Address not found")
                }
        except Exception as e:
            logger.error(f"Error validating address: {e}")
            return {
                "valid": False,
                "confidence": 0,
                "error": str(e)
            }
    
    async def validate_npi(self, npi: str, original_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Validate NPI through NPI Registry API.
        Extract provider name, taxonomy/specialty, practice address.
        Compare with CSV and produce partial match score.
        
        Args:
            npi: National Provider Identifier
            original_data: Original CSV data for comparison
            
        Returns:
            Dictionary with validation results and confidence
        """
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "number": npi,
                    "version": "2.1"
                }
                
                async with session.get(NPI_REGISTRY_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("result_count", 0) > 0:
                            result = data.get("results", [])[0]
                            
                            # Extract provider information
                            provider_info = {}
                            
                            # Basic info
                            basic = result.get("basic", {})
                            provider_info["first_name"] = basic.get("first_name")
                            provider_info["last_name"] = basic.get("last_name")
                            provider_info["organization_name"] = basic.get("organization_name")
                            provider_info["provider_type"] = basic.get("enumeration_type")
                            
                            # Addresses
                            addresses = result.get("addresses", [])
                            if addresses:
                                primary_address = addresses[0]
                                provider_info["address_line1"] = primary_address.get("address_1")
                                provider_info["address_line2"] = primary_address.get("address_2")
                                provider_info["city"] = primary_address.get("city")
                                provider_info["state"] = primary_address.get("state")
                                provider_info["zip_code"] = primary_address.get("postal_code")
                                provider_info["phone"] = primary_address.get("telephone_number")
                            
                            # Taxonomies (specialties)
                            taxonomies = result.get("taxonomies", [])
                            if taxonomies:
                                provider_info["specialty"] = taxonomies[0].get("desc")
                            
                            # Calculate confidence based on match with original data
                            confidence = 100  # Start with high confidence
                            match_score = 0
                            total_fields = 0
                            
                            if original_data:
                                # Compare key fields
                                comparison_fields = {
                                    "first_name": provider_info.get("first_name"),
                                    "last_name": provider_info.get("last_name"),
                                    "city": provider_info.get("city"),
                                    "state": provider_info.get("state")
                                }
                                
                                for field, api_value in comparison_fields.items():
                                    if api_value:
                                        total_fields += 1
                                        csv_value = original_data.get(field)
                                        if csv_value:
                                            if str(csv_value).strip().lower() == str(api_value).strip().lower():
                                                match_score += 1
                                
                                # Calculate partial match score
                                if total_fields > 0:
                                    match_ratio = match_score / total_fields
                                    confidence = int(100 * match_ratio)
                                    if confidence < 50:
                                        confidence = 50  # Minimum confidence if NPI found
                            
                            return {
                                "valid": True,
                                "data": provider_info,
                                "confidence": confidence,
                                "match_score": match_score,
                                "total_fields": total_fields
                            }
                        else:
                            return {
                                "valid": False,
                                "error": "NPI not found in registry",
                                "confidence": 0
                            }
                    else:
                        return {
                            "valid": False,
                            "error": f"API error: {response.status}",
                            "confidence": 0
                        }
        except Exception as e:
            logger.error(f"Error validating NPI {npi}: {e}")
            return {
                "valid": False,
                "error": str(e),
                "confidence": 0
            }
    
    async def scrape_website(self, url: str) -> Dict[str, Any]:
        """
        Scrape provider website using BeautifulSoup or Selenium.
        Extract specialty, phone, clinic name.
        
        Args:
            url: Website URL
            
        Returns:
            Dictionary with scraped data and confidence
        """
        try:
            # Verify website exists first
            website_exists = await verify_website_exists(url)
            if not website_exists:
                return {
                    "valid": False,
                    "confidence": 0,
                    "error": "Website not accessible"
                }
            
            # Scrape website
            website_data = await scrape_provider_website(url)
            
            if website_data.get("success") and website_data.get("data"):
                extracted_data = website_data["data"]
                
                # Calculate confidence based on data extracted
                confidence = 0
                if extracted_data.get("phone"):
                    confidence += 30
                if extracted_data.get("specialty_info") or extracted_data.get("practice_name"):
                    confidence += 30
                if extracted_data.get("email"):
                    confidence += 20
                if extracted_data.get("address"):
                    confidence += 20
                
                return {
                    "valid": True,
                    "data": extracted_data,
                    "confidence": min(confidence, 100)
                }
            else:
                return {
                    "valid": False,
                    "confidence": 0,
                    "error": website_data.get("error", "Failed to scrape website")
                }
        except Exception as e:
            logger.error(f"Error scraping website {url}: {e}")
            return {
                "valid": False,
                "confidence": 0,
                "error": str(e)
            }
