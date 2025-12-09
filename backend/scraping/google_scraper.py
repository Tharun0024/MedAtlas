"""
Google Places API scraper for address validation and enrichment.
"""

import os
import aiohttp
import asyncio
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

# Google Places API key (should be in environment variable)
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")


async def validate_address_google(address: str, city: str = "", state: str = "", zip_code: str = "") -> Dict[str, Any]:
    """
    Validate address using Google Places API.
    
    Args:
        address: Street address
        city: City name
        state: State code
        zip_code: ZIP code
        
    Returns:
        Dictionary with validation results and normalized address
    """
    if not GOOGLE_PLACES_API_KEY:
        logger.warning("Google Places API key not configured")
        return {
            "valid": False,
            "error": "API key not configured",
            "normalized_address": None
        }
    
    # Build query
    query_parts = [address]
    if city:
        query_parts.append(city)
    if state:
        query_parts.append(state)
    if zip_code:
        query_parts.append(zip_code)
    
    query = ", ".join(query_parts)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Use Places API Text Search
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                "query": query,
                "key": GOOGLE_PLACES_API_KEY
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("status") == "OK" and data.get("results"):
                        result = data["results"][0]
                        location = result.get("geometry", {}).get("location", {})
                        
                        # Get place details for full address
                        place_id = result.get("place_id")
                        if place_id:
                            details = await get_place_details(place_id, session)
                            formatted_address = details.get("formatted_address", result.get("formatted_address"))
                            
                            return {
                                "valid": True,
                                "formatted_address": formatted_address,
                                "latitude": location.get("lat"),
                                "longitude": location.get("lng"),
                                "place_id": place_id,
                                "normalized_address": parse_address(formatted_address)
                            }
                    
                    return {
                        "valid": False,
                        "error": "Address not found",
                        "normalized_address": None
                    }
                else:
                    return {
                        "valid": False,
                        "error": f"API error: {response.status}",
                        "normalized_address": None
                    }
    except Exception as e:
        logger.error(f"Error validating address: {e}")
        return {
            "valid": False,
            "error": str(e),
            "normalized_address": None
        }


async def get_place_details(place_id: str, session: Optional[aiohttp.ClientSession] = None) -> Dict[str, Any]:
    """
    Get detailed place information from Google Places API.
    
    Args:
        place_id: Google Place ID
        session: Optional aiohttp session
        
    Returns:
        Place details dictionary
    """
    if not GOOGLE_PLACES_API_KEY:
        return {}
    
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "formatted_address,address_components,geometry,phone_number,website",
        "key": GOOGLE_PLACES_API_KEY
    }
    
    try:
        if session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "OK":
                        return data.get("result", {})
        else:
            async with aiohttp.ClientSession() as new_session:
                async with new_session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "OK":
                            return data.get("result", {})
    except Exception as e:
        logger.error(f"Error getting place details: {e}")
    
    return {}


def parse_address(formatted_address: str) -> Dict[str, str]:
    """
    Parse formatted address into components.
    
    Args:
        formatted_address: Formatted address string
        
    Returns:
        Dictionary with address components
    """
    parts = formatted_address.split(",")
    normalized = {}
    
    if len(parts) >= 3:
        normalized["address_line1"] = parts[0].strip()
        normalized["city"] = parts[1].strip()
        
        # Parse state and ZIP from last part
        last_part = parts[-1].strip()
        state_zip = last_part.split()
        if len(state_zip) >= 2:
            normalized["state"] = state_zip[0]
            normalized["zip_code"] = state_zip[1]
    
    return normalized

