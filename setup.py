"""
Setup script for MedAtlas.
"""

from setuptools import setup, find_packages

setup(
    name="medatlas",
    version="1.0.0",
    description="AI-powered Provider Data Validation & Directory Management Platform",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "pandas>=2.1.3",
        "aiohttp>=3.9.1",
        "beautifulsoup4>=4.12.2",
        "pytesseract>=0.3.10",
        "pdf2image>=1.16.3",
        "Pillow>=10.1.0",
        "phonenumbers>=8.13.25",
        "pydantic>=2.5.0",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.9",
)

