# MedAtlas Quick Start Guide

## Prerequisites Checklist

- [ ] Python 3.9+ installed
- [ ] Node.js 18+ installed
- [ ] Tesseract OCR installed (for PDF processing)
- [ ] Google Places API key (optional, for address validation)
- [ ] NPI Registry API access (free, no key needed)

## Quick Setup (5 minutes)

### 1. Backend Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database (creates medatlas.db)
python -c "from backend.database import init_database; init_database()"

# Set up environment variables (create .env file)
echo "GOOGLE_PLACES_API_KEY=your_key_here" > .env
echo "TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe" >> .env  # Windows only
```

### 2. Frontend Setup

```bash
cd frontend
npm install
```

### 3. Start the Application

**Terminal 1 - Backend:**
```bash
python run_backend.py
```
Backend will run on http://localhost:8000

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```
Frontend will run on http://localhost:5173

### 4. Test the Application

1. Open http://localhost:5173 in your browser
2. Navigate to Upload page
3. Upload the example CSV file: `example_providers.csv`
4. Go to Providers page and click "Validate" on a provider
5. Check Discrepancies page for any flagged issues
6. View Reports page for analytics

## Testing the API Directly

```bash
# Health check
curl http://localhost:8000/health

# Get providers
curl http://localhost:8000/api/providers

# Get summary
curl http://localhost:8000/api/summary
```

## Common Issues

### Issue: ModuleNotFoundError: No module named 'backend'
**Solution:** Make sure you're running from the project root directory, or use `python run_backend.py`

### Issue: Tesseract not found
**Solution:** 
- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
- macOS: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`
- Set TESSERACT_CMD in .env file

### Issue: Port already in use
**Solution:** Change ports in `run_backend.py` (backend) or `vite.config.js` (frontend)

### Issue: CORS errors
**Solution:** Make sure backend is running on port 8000 and frontend proxy is configured correctly

## Next Steps

1. Upload your own provider CSV file
2. Configure Google Places API key for better address validation
3. Customize agents for your specific use case
4. Set up PostgreSQL for production (see README.md)

## Getting Help

- Check README.md for detailed documentation
- Review API endpoints in backend/api/endpoints/
- Examine agent implementations in backend/agents/

