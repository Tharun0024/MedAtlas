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
