"""
OCR module for MedAtlas.
"""

from .pdf_extractor import extract_text_from_pdf, extract_from_pdf_bytes, parse_provider_data

__all__ = [
    "extract_text_from_pdf",
    "extract_from_pdf_bytes",
    "parse_provider_data"
]

