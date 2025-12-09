"""
Website scraper for provider information extraction.
"""

import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Optional, Any
import logging
import re
import asyncio

logger = logging.getLogger(__name__)


async def scrape_provider_website(url: str) -> Dict[str, Any]:
    """
    Scrape provider website for information.
    
    Args:
        url: Website URL
        
    Returns:
        Dictionary with scraped information
    """
    if not url or not url.startswith(('http://', 'https://')):
        return {"error": "Invalid URL"}
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    extracted = {}
                    
                    # Extract phone number
                    phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
                    phone_matches = re.findall(phone_pattern, html)
                    if phone_matches:
                        extracted["phone"] = phone_matches[0]
                    
                    # Extract email
                    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                    email_matches = re.findall(email_pattern, html)
                    if email_matches:
                        extracted["email"] = email_matches[0]
                    
                    # Extract address (look for common address patterns)
                    address_patterns = [
                        r'\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Circle|Cir)[\s,]+[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}',
                    ]
                    for pattern in address_patterns:
                        matches = re.findall(pattern, html, re.IGNORECASE)
                        if matches:
                            extracted["address"] = matches[0]
                            break
                    
                    # Extract specialty information
                    specialty_keywords = [
                        "specialty", "specialties", "practice", "services",
                        "cardiology", "orthopedics", "pediatrics", "dermatology"
                    ]
                    for keyword in specialty_keywords:
                        elements = soup.find_all(string=re.compile(keyword, re.I))
                        if elements:
                            # Try to extract nearby text
                            for elem in elements[:3]:
                                parent = elem.parent
                                if parent:
                                    text = parent.get_text(strip=True)
                                    if len(text) < 200:
                                        extracted["specialty_info"] = text
                                        break
                            break
                    
                    # Extract practice name from title or h1
                    title = soup.find('title')
                    if title:
                        extracted["practice_name"] = title.get_text(strip=True)
                    
                    h1 = soup.find('h1')
                    if h1 and not extracted.get("practice_name"):
                        extracted["practice_name"] = h1.get_text(strip=True)
                    
                    return {
                        "success": True,
                        "data": extracted
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}"
                    }
    except asyncio.TimeoutError:
        logger.error(f"Timeout scraping {url}")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return {"success": False, "error": str(e)}


async def verify_website_exists(url: str) -> bool:
    """
    Verify if website URL is accessible.
    
    Args:
        url: Website URL
        
    Returns:
        True if website is accessible
    """
    if not url or not url.startswith(('http://', 'https://')):
        return False
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5), allow_redirects=True) as response:
                return response.status == 200
    except:
        return False

