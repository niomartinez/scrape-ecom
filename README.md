# SheetScrape - Web Scraping Add-on for Google Sheets

![SheetScrape Logo](https://via.placeholder.com/200x60?text=SheetScrape)

**Tagline:** Unlock Web Data, Directly in Your Google Sheets.

## Overview

SheetScrape is a powerful Google Sheets™ add-on that allows users to extract structured data from websites directly into spreadsheets without any coding required. By simply providing a URL and specifying desired data points, users can automate data collection at scale with a single formula.

Key features:
- Extract 70+ data points from Amazon product pages across 18 marketplaces
- Automatically fill spreadsheet cells with a single formula: `=SCRAPE(url, selectors)`
- Built for scale - process hundreds of ASINs with one click-and-drag
- Simple, no-code interface for anyone comfortable with spreadsheets
- Three optimized functions: `SCRAPE()`, `SCRAPE_BASIC()`, and `SCRAPE_MEDIUM()`

## Project Structure

This repository contains both the backend API and Google Apps Script frontend:

```
/
├── Apps Scripts/               # Google Apps Script frontend
│   ├── SheetScrape.js          # Main Apps Script code
│   ├── appsscript.json         # Manifest file
│   └── README.md               # Frontend documentation
├── src/                        # Python backend
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── selectors/              # Selector definitions
│   │   ├── __init__.py
│   │   └── amazon.py           # Amazon-specific selectors (70+ selectors)
│   └── utils/                  # Utility modules
│       ├── __init__.py
│       └── scraping.py         # Scraping utilities (Playwright + BeautifulSoup)
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── render.yaml                 # Render deployment config
├── Procfile                    # Heroku deployment config
└── README.md                   # This file
```

## Backend Setup

The backend is a Python FastAPI application that handles web scraping requests using Playwright for JavaScript-heavy sites and BeautifulSoup for simple HTML parsing.

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
   playwright install chromium
   ```

5. Set up environment variables by copying `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` and set your values:
   ```
   SECRET_API_KEY="your-super-secret-key"
   PORT=8000
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
- `GET /cache/stats` - Get cache statistics (if Redis enabled)
- `POST /cache/clear` - Clear the cache (if Redis enabled)

## Frontend Setup

The frontend is a Google Apps Script that adds custom functions to Google Sheets.

### Deployment

1. Open Google Sheets and go to Extensions > Apps Script
2. Copy the contents of `Apps Scripts/SheetScrape.js` into the editor
3. Update the `API_URL` constant to point to your deployed backend
4. Save the script and reload your sheet

For detailed deployment instructions, see `Apps Scripts/README.md`.

## Usage

### Quick Start

1. **Set API Key**: In Google Sheets, use SheetScrape > Account > Set API Key
2. **Setup Sheet**: Click SheetScrape > Setup/Reset Sheet for ideal layout
3. **Add ASINs**: Enter Amazon ASINs in column A starting from A5
4. **Choose Function**:
   - `=SCRAPE_BASIC(B5)` - 8 essential fields (Title, BP1-5, Description, Image)
   - `=SCRAPE_MEDIUM(B5)` - 13 important fields (Title, BP1-6, Description, Images 1-5)
   - `=SCRAPE(B5, D4:AE4)` - Custom selection using header dropdowns
5. **Scale Up**: Drag the formula down to process all ASINs

### Available Data Points

SheetScrape supports 70+ Amazon selectors including:

**Basic Information:**
- title, asin, url, sale_price, list_price, rating, review_count

**Product Details:**
- brand_name, manufacturer, model, color_name, style_name, description
- bullet_point_1 through bullet_point_6, bullet_points

**Images & Media:**
- image_1_source through image_6_source, featured_image_source, has_video

**Dimensions & Specifications:**
- item_weight, item_dimensions, package_dimensions, capacity

**Marketplace Data:**
- availability, ships_from, best_seller_rank_1, best_seller_rank_2
- categories, times_evaluated, variations_asins

**Special Features:**
- has_deal, has_coupon, coupon_value, has_climate_pledge
- buybox_winner, offers_count

### Supported Amazon Marketplaces

- amazon.com (United States)
- amazon.ca (Canada)
- amazon.com.mx (Mexico)
- amazon.com.br (Brazil)
- amazon.co.uk (United Kingdom)
- amazon.fr (France)
- amazon.de (Germany)
- amazon.nl (Netherlands)
- amazon.es (Spain)
- amazon.it (Italy)
- amazon.com.tr (Turkey)
- amazon.in (India)
- amazon.sa (Saudi Arabia)
- amazon.ae (UAE)
- amazon.eg (Egypt)
- amazon.co.jp (Japan)
- amazon.com.au (Australia)
- amazon.sg (Singapore)

## Production Deployment

### Backend Deployment Options

**Render (Recommended):**
- Uses included `render.yaml` configuration
- Automatic deployments from GitHub
- Built-in environment variable management

**Docker:**
- Uses included `Dockerfile`
- Supports any Docker-compatible platform

**Heroku:**
- Uses included `Procfile`
- Easy deployment with Heroku CLI

### Environment Variables for Production

```
SECRET_API_KEY=your-production-api-key
PORT=10000
REDIS_URL=your-redis-url  # For caching
```

## Performance & Optimization

- **Caching**: 6-hour Redis cache for repeated requests
- **Timeout Management**: 25-second API timeout with 5-second buffer for Google Sheets
- **Selector Limits**: Maximum 30 selectors per request to prevent timeouts
- **Anti-Detection**: Realistic browser headers and human-like behavior patterns
- **Fallback Strategy**: Playwright for JS-heavy sites, BeautifulSoup for simple HTML

## License

[MIT](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions:
1. Check the documentation in `Apps Scripts/README.md`
2. Review the implementation guide in `implementation_guide.md`
3. Open an issue on GitHub