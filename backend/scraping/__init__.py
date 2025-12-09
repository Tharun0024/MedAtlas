"""
Scraping module for MedAtlas.
"""

from .google_scraper import validate_address_google, get_place_details
from .website_scraper import scrape_provider_website, verify_website_exists
from .license_scraper import verify_license, scrape_state_board

__all__ = [
    "validate_address_google",
    "get_place_details",
    "scrape_provider_website",
    "verify_website_exists",
    "verify_license",
    "scrape_state_board"
]

