# MedAtlas

AI-powered Provider Data Validation & Directory Management Platform for healthcare payers.

## Overview

MedAtlas is a comprehensive full-stack system that validates, enriches, and manages healthcare provider data through a 4-agent AI pipeline. The platform processes CSV files and PDF documents, validates provider information through multiple APIs, and provides a modern dashboard for review and management.

## Features

- **CSV & PDF Upload**: Upload provider CSV files and scanned PDF documents
- **4-Agent AI Pipeline**:
  - **Data Validation Agent**: Validates NPI, phone, address, and website
  - **Enrichment Agent**: Extracts data from PDFs via OCR and enriches from websites
  - **QA Agent**: Compares data sources and detects inconsistencies
  - **Directory Management Agent**: Finalizes profiles and exports directories
- **API Integration**: NPI Registry API, Google Places API
- **OCR Processing**: Tesseract-based PDF text extraction
- **Web Scraping**: BeautifulSoup + Selenium for data enrichment
- **Modern Dashboard**: React-based UI with charts and analytics
- **Discrepancy Tracking**: Flag and resolve data inconsistencies
- **Export Capabilities**: Export validated directories as CSV or JSON

## Tech Stack

### Backend
- **Framework**: FastAPI
- **Database**: SQLite (prototype, ready for PostgreSQL migration)
- **Agents**: Custom agent classes (ready for LangGraph/CrewAI integration)
- **Scraping**: BeautifulSoup + Selenium
- **OCR**: Tesseract (pytesseract)
- **APIs**: NPI Registry API, Google Places API

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Charts**: Recharts
- **Routing**: React Router

## Installation

### Prerequisites

- Python 3.9+
- Node.js 18+
- Tesseract OCR (for PDF extraction)
  - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
  - macOS: `brew install tesseract`
  - Linux: `sudo apt-get install tesseract-ocr`

### Backend Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (create `.env` file):
```env
GOOGLE_PLACES_API_KEY=your_google_places_api_key
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe  # Windows only
```

4. Initialize the database:
```bash
python -c "from backend.database import init_database; init_database()"
```

5. Run the FastAPI server:
```bash
# Option 1: Use the startup script (recommended)
python run_backend.py

# Option 2: Run directly
cd backend/api
python main.py

# Option 3: Use uvicorn directly
uvicorn backend.api.main:app --reload --port 8000
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Usage

### 1. Upload Provider Data

- Navigate to the Upload page
- Upload a CSV file with provider data (see CSV format requirements)
- Optionally upload PDF documents for OCR extraction

### 2. Validate Providers

- Go to the Providers page
- Click "Validate" on any provider to run the validation pipeline
- View confidence scores and validation status

### 3. Review Discrepancies

- Navigate to the Discrepancies page
- Review flagged inconsistencies between CSV, API, and scraped data
- Resolve discrepancies manually

### 4. View Reports

- Go to the Reports page
- View analytics and charts
- Export validated directories as CSV or JSON

### CSV Format

Your CSV file should include these columns:
- NPI
- First Name, Last Name
- Organization Name
- Provider Type, Specialty
- Address Line 1, Address Line 2
- City, State, ZIP Code
- Phone, Email, Website
- License Number, License State
- Practice Name

## API Endpoints

### Providers
- `POST /api/upload` - Upload provider CSV
- `GET /api/providers` - Get all providers
- `GET /api/provider/{id}` - Get provider by ID
- `GET /api/summary` - Get summary statistics

### Validation
- `POST /api/validate` - Validate a provider
- `POST /api/upload-pdf` - Upload PDF for OCR

### Discrepancies
- `GET /api/discrepancies` - Get discrepancies
- `GET /api/discrepancies/{id}` - Get discrepancy by ID
- `PATCH /api/discrepancies/{id}` - Update discrepancy

### Export
- `POST /api/export` - Export directory
- `GET /api/export/download/{filename}` - Download export file

## Pipeline Orchestrator

Run the full pipeline programmatically:

```python
from main import PipelineOrchestrator

orchestrator = PipelineOrchestrator()

# Process a single provider
result = await orchestrator.process_provider(provider_id=1)

# Process all providers
results = await orchestrator.process_all_providers(limit=100)

# Process from CSV
results = await orchestrator.process_from_csv("data/providers.csv")
```

## Database Schema

### Providers Table
- Basic provider information (NPI, name, address, contact)
- Confidence and risk scores
- Validation status
- Raw, validated, and enriched data (JSON)

### Discrepancies Table
- Field-level discrepancies
- CSV, API, and scraped values
- Confidence and risk levels
- Resolution status

### Logs Table
- Event logging
- Agent activity tracking
- Audit trail

## Future Enhancements

- [ ] LangGraph/CrewAI integration for agent orchestration
- [ ] PostgreSQL migration
- [ ] Advanced ML-based data matching
- [ ] Real-time validation webhooks
- [ ] Multi-user authentication
- [ ] Batch processing optimization
- [ ] State-specific license verification integration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.

