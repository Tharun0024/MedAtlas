"""
PDF extraction using OCR (Tesseract) for scanned documents.
"""

import os
import logging
from typing import Dict, List, Optional, Any
import pdf2image
from PIL import Image
import pytesseract
import io

logger = logging.getLogger(__name__)

# Configure Tesseract path (Windows)
# For Linux/Mac, this can be removed or set to None
TESSERACT_CMD = os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if TESSERACT_CMD and os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def extract_text_from_pdf(pdf_path: str, dpi: int = 300) -> Dict[str, Any]:
    """
    Extract text from PDF using OCR.
    
    Args:
        pdf_path: Path to PDF file
        dpi: DPI for image conversion (higher = better quality but slower)
        
    Returns:
        Dictionary with extracted text and metadata
    """
    try:
        # Convert PDF to images
        images = pdf2image.convert_from_path(pdf_path, dpi=dpi)
        
        extracted_text = []
        page_data = []
        
        for i, image in enumerate(images):
            # Perform OCR
            text = pytesseract.image_to_string(image, lang='eng')
            extracted_text.append(text)
            
            # Extract structured data
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            page_data.append({
                "page_number": i + 1,
                "text": text,
                "word_count": len(text.split()),
                "data": data
            })
        
        full_text = "\n\n".join(extracted_text)
        
        # Try to extract structured information
        structured_data = parse_provider_data(full_text)
        
        return {
            "success": True,
            "full_text": full_text,
            "page_count": len(images),
            "pages": page_data,
            "structured_data": structured_data
        }
    
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return {
            "success": False,
            "error": str(e),
            "full_text": "",
            "structured_data": {}
        }


def parse_provider_data(text: str) -> Dict[str, Any]:
    """
    Parse extracted text to find provider information.
    
    Args:
        text: Extracted text from OCR
        
    Returns:
        Dictionary with parsed provider data
    """
    import re
    
    parsed = {}
    
    # Extract NPI (10 digits)
    npi_pattern = r'\b\d{10}\b'
    npi_matches = re.findall(npi_pattern, text)
    if npi_matches:
        # Look for "NPI" label nearby
        for match in npi_matches:
            idx = text.find(match)
            context = text[max(0, idx-20):idx+30].lower()
            if 'npi' in context:
                parsed["npi"] = match
                break
    
    # Extract phone numbers
    phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    phone_matches = re.findall(phone_pattern, text)
    if phone_matches:
        parsed["phone"] = phone_matches[0]
    
    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_matches = re.findall(email_pattern, text)
    if email_matches:
        parsed["email"] = email_matches[0]
    
    # Extract addresses
    address_pattern = r'\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr)[\s,]+[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}'
    address_matches = re.findall(address_pattern, text, re.IGNORECASE)
    if address_matches:
        parsed["address"] = address_matches[0]
    
    # Extract names (look for title patterns)
    name_patterns = [
        r'Dr\.\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
        r'([A-Z][a-z]+\s+[A-Z][a-z]+),\s*M\.D\.',
        r'([A-Z][a-z]+\s+[A-Z][a-z]+),\s*DO'
    ]
    for pattern in name_patterns:
        matches = re.findall(pattern, text)
        if matches:
            parsed["name"] = matches[0]
            break
    
    # Extract license numbers (varies by state)
    license_patterns = [
        r'License[:\s]+([A-Z0-9-]+)',
        r'License\s+Number[:\s]+([A-Z0-9-]+)',
        r'Lic\.\s+#[:\s]*([A-Z0-9-]+)'
    ]
    for pattern in license_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            parsed["license_number"] = matches[0]
            break
    
    return parsed


def extract_from_pdf_bytes(pdf_bytes: bytes, dpi: int = 300) -> Dict[str, Any]:
    """
    Extract text from PDF bytes.
    
    Args:
        pdf_bytes: PDF file as bytes
        dpi: DPI for image conversion
        
    Returns:
        Dictionary with extracted text and metadata
    """
    # Save to temporary file
    import tempfile
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(pdf_bytes)
        tmp_path = tmp_file.name
    
    try:
        result = extract_text_from_pdf(tmp_path, dpi)
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    
    return result

