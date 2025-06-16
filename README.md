# SheetScrape - Web Scraping Add-on for Google Sheets

![SheetScrape Logo](https://via.placeholder.com/200x60?text=SheetScrape)

**Tagline:** Unlock Web Data, Directly in Your Google Sheets.

## Overview

SheetScrape is a powerful Google Sheets™ add-on that allows users to extract structured data from websites directly into spreadsheets without any coding required. By simply providing a URL and specifying desired data points, users can automate data collection at scale with a single formula.

Key features:
- Extract 80+ data points from Amazon product pages across 18 marketplaces
- Automatically fill spreadsheet cells with a single formula
- Built for scale - process hundreds of ASINs with one click-and-drag
- Simple, no-code interface for anyone comfortable with spreadsheets

## Project Structure

This repository contains both the backend API and Google Apps Script frontend:

```
/
├── Apps Scripts/               # Google Apps Script frontend
│   ├── SheetScrape.js          # Main Apps Script code
│   ├── appsscript.json         # Manifest file
│   ├── README.md               # Frontend documentation
│   └── DEPLOYMENT.md           # Frontend deployment guide
├── src/                        # Python backend
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── selectors/              # Selector definitions
│   │   ├── __init__.py
│   │   └── amazon.py           # Amazon-specific selectors
│   └── utils/                  # Utility modules
│       ├── __init__.py
│       └── scraping.py         # Scraping utilities
├── .env                        # Environment variables (secret)
└── requirements.txt            # Python dependencies
```

## Backend Setup

The backend is a Python FastAPI application that handles web scraping requests.

### Prerequisites

- Python 3.8 or higher
- pip
- Playwright (for JavaScript-heavy sites)
- Redis (optional, for caching)

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/scrape-ecom.git
   cd scrape-ecom
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install the Playwright browsers:
   ```bash
   playwright install
   ```

5. Set up environment variables in `.env`:
   ```
   SECRET_API_KEY="your-super-secret-key"
   REDIS_URL="redis://localhost:6379/0"  # Optional, for caching
   ```

### Running the Backend

Start the development server:

```bash
uvicorn src.main:app --reload --port 8000
```

The API will be available at http://127.0.0.1:8000.

API Documentation will be available at http://127.0.0.1:8000/docs.

### API Endpoints

- `POST /scrape` - Main endpoint for scraping data
- `GET /health` - Health check endpoint
- `GET /cache/stats` - Get cache statistics
- `POST /cache/clear` - Clear the cache

## Frontend Setup

The frontend is a Google Apps Script that adds the `=SCRAPE()` function to Google Sheets.

### Deployment

1. Open Google Sheets and go to Extensions > Apps Script
2. Copy the contents of `Apps Scripts/SheetScrape.js` into the editor
3. Update the `API_URL` constant to point to your deployed backend
4. Save the script and reload your sheet

For detailed deployment instructions, see `Apps Scripts/DEPLOYMENT.md`.

## Usage

1. Get your API key from the backend setup
2. In Google Sheets, open the "SheetScrape" menu
3. Select "Account > Set API Key" and enter your API key
4. Click "Setup/Reset Sheet" to create the ideal layout
5. Add Amazon ASINs in column A starting from A5
6. The formula `=SCRAPE(B5, C$4:Z$4)` in cell C5 will fetch all selected data
7. Drag the formula down to process all ASINs

## Production Deployment

For production use, we recommend:

1. Deploy the backend to a cloud provider like Heroku, AWS, or Google Cloud
2. Set up a proper database for user management and API keys
3. Configure Redis for caching
4. Use a rotating proxy service for reliable scraping
5. Publish the Add-on to the Google Workspace Marketplace

## License

[MIT](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.