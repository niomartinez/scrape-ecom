# Full Implementation Guide: Building SheetScrape

This guide will walk you through creating SheetScrape, a powerful Google Sheets add-on for web scraping. We will build:

- A Python Backend API using FastAPI that handles the actual web scraping
- A Google Apps Script Frontend that provides custom functions (`=SCRAPE()`, `=SCRAPE_BASIC()`, `=SCRAPE_MEDIUM()`) and helper menus within your spreadsheet

## Architecture Overview

The process works like this:

1. User types `=SCRAPE(url, headers_range)` or `=SCRAPE_BASIC(url)` into a Google Sheet
2. Google Apps Script calls your backend API, sending the URL and the list of requested data points (e.g., `["title", "sale_price"]`)
3. Python Backend API receives the request
4. The API scrapes the webpage using Playwright (for JavaScript-heavy sites) or BeautifulSoup (for simple HTML), extracts the requested data points in order, and returns them as a JSON array
5. Google Apps Script receives the JSON data and displays it in the sheet. Google Sheets automatically "spills" the array into the adjacent cells

## Prerequisites

Before you start, make sure you have:

- Python 3.8+ installed
- A code editor like Cursor
- A Google Account

## Part 1: The Backend API (Python & FastAPI)

This is the engine of your tool. We'll set up a web server that listens for requests from Google Sheets.

### Step 1.1: Project Setup

1. Create a new project folder (e.g., `scrape-ecom`)
2. Open this folder in Cursor
3. Create a file named `requirements.txt` and add the dependencies:

```txt
fastapi==0.104.0
uvicorn[standard]==0.23.2
requests==2.31.0
beautifulsoup4==4.12.2
python-dotenv==1.0.0
lxml==4.9.3
playwright==1.39.0
redis==5.0.1
```

4. Create a file named `.env` to store your secret API key. This keeps it out of your code:

```env
SECRET_API_KEY="your-super-secret-key-123"
PORT=8000
PYTHON_VERSION=3.11.0
# REDIS_URL=redis://localhost:6379/0
```

5. Open the terminal in Cursor (Cmd/Ctrl + J) and create a virtual environment:

```bash
# Create the virtual environment
python3 -m venv venv

# Activate it (macOS/Linux)
source venv/bin/activate
# Or on Windows
# venv\Scripts\activate
```

6. Install the dependencies:

```bash
pip install -r requirements.txt
playwright install chromium
```

### Step 1.2: Create the Main Application File

Create a file named `src/main.py`. This will contain all of your API logic:

```python
import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import json
import time
import redis
from functools import lru_cache

from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import our modules
from src.selectors.amazon import get_selectors_for_domain
from src.utils.scraping import (
    choose_scraping_method,
    extract_specific_selectors,
    ScrapingError
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Redis for caching (if available)
REDIS_URL = os.getenv('REDIS_URL')
redis_client = None
if REDIS_URL:
    try:
        redis_client = redis.from_url(REDIS_URL)
        logger.info("Redis cache initialized")
    except Exception as e:
        logger.warning(f"Redis initialization failed: {e}. Caching disabled.")

# --- Models for API Data Structure ---
class ScrapeRequest(BaseModel):
    url: str
    selectors: List[str]
    marketplace: str = Field(default="Amazon.com", description="The marketplace to scrape from")
    force_refresh: bool = Field(default=False, description="Force a fresh scrape instead of using cache")

# --- Authentication ---
SECRET_KEY = os.getenv("SECRET_API_KEY")
if not SECRET_KEY:
    logger.warning("SECRET_API_KEY not found in environment!")

async def verify_api_key(x_api_key: str = Header(...)):
    """Verifies that the API key in the request header is valid."""
    if not SECRET_KEY or x_api_key != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

# --- FastAPI Application ---
app = FastAPI(
    title="SheetScrape API",
    description="An API to scrape web data for the SheetScrape Google Sheets Add-on.",
    version="1.0.0",
)

# Add CORS middleware to allow requests from Google Apps Script
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Google Apps Script compatibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"status": "online", "message": "SheetScrape API is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time()
    }

@app.post("/scrape", dependencies=[Depends(verify_api_key)])
async def scrape_url(request: ScrapeRequest):
    """
    Receives a URL and a list of selectors, scrapes the page, and returns the data.
    
    If Redis is configured, results are cached for 6 hours unless force_refresh is True.
    """
    url = request.url
    selectors = request.selectors
    marketplace = request.marketplace
    force_refresh = request.force_refresh
    
    logger.info(f"Processing request for URL: {url} in marketplace: {marketplace}")
    logger.info(f"Requested selectors: {selectors}")
    
    # Check for cached result if Redis is available
    if redis_client and not force_refresh:
        cache_key = f"sheetscrape:{url}:{','.join(selectors)}:{marketplace}"
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.info(f"Returning cached data for {url}")
            try:
                cached_result = json.loads(cached_data)
                return {"data": cached_result}
            except json.JSONDecodeError:
                logger.warning("Failed to parse cached data, proceeding with fresh scrape")
    
    # Scrape the URL
    try:
        html_content = await choose_scraping_method(url)
        logger.info(f"Successfully scraped HTML content, length: {len(html_content)} characters")
    except Exception as e:
        logger.error(f"Failed to scrape {url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")
    
    # Get selectors for the domain
    domain_selectors = get_selectors_for_domain(url, marketplace)
    logger.info(f"Using {len(domain_selectors)} available selectors for domain")
    
    # Extract the requested data
    extracted_data = extract_specific_selectors(html_content, selectors, domain_selectors)
    logger.info(f"Extraction results: {[item[:50] + '...' if len(str(item)) > 50 else item for item in extracted_data]}")
    
    # Prepare response data as a 2D array for Google Sheets spilling
    response_data = [extracted_data]
    
    # Cache the result if Redis is available (cache for 6 hours)
    if redis_client:
        try:
            redis_client.setex(cache_key, 21600, json.dumps(response_data))  # 6 hours cache
            logger.info(f"Cached result for {url}")
        except Exception as e:
            logger.warning(f"Failed to cache result: {str(e)}")
    
    logger.info(f"Returning response: {{'data': {[item[:30] + '...' if len(str(item)) > 30 else item for item in response_data[0]]}}}")
    return {"data": response_data}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
```

### Step 1.3: Run the Backend Locally

In your activated terminal, run the following command:

```bash
uvicorn src.main:app --reload
```

Your API is now running at `http://127.0.0.1:8000`. You can see the auto-generated documentation at `http://127.0.0.1:8000/docs`.

## Part 2: The Frontend (Google Apps Script)

This script lives inside your Google Sheet and connects to your backend.

### Step 2.1: Create the Apps Script

1. Open a new Google Sheet
2. Go to Extensions > Apps Script
3. A new editor will open. Replace the content of `Code.gs` with the code below:

```javascript
// --- Configuration ---
// This should point to your backend API. Use your local URL for testing.
// When you deploy, change this to your live server URL.
const API_URL = "http://127.0.0.1:8000/scrape";

// Define the standard header order that matches our backend selectors (28 columns + 1 blank)
const STANDARD_HEADERS = [
  'title', 'bullet_point_1', 'bullet_point_2', 'bullet_point_3', 'bullet_point_4',
  'bullet_point_5', 'bullet_points', 'description', 'a_plus_content', 'availability',
  'brand_name', 'buybox_winner', 'buybox_winner_link', 'variations_asins',
  'best_seller_category', 'best_seller_rank_1', 'best_seller_rank_2', 'times_evaluated',
  'asin', 'categories', 'image_1_source', 'image_2_source', 'image_3_source',
  'image_4_source', 'image_5_source', 'image_6_source', 'has_video', ''
];

// All available selectors for dropdown validation - users can change to any of these
const ALL_SELECTORS = [
  'title', 'asin', 'url', 'sale_price', 'list_price', 'sale_price_per_unit',
  'rating', 'review_count', 'times_evaluated', 'availability', 'ships_from',
  'brand_name', 'manufacturer', 'model', 'color_name', 'style_name',
  'country_of_origin', 'description', 'bullet_points', 'bullet_point_1',
  'bullet_point_2', 'bullet_point_3', 'bullet_point_4', 'bullet_point_5',
  'bullet_point_6', 'image_1_source', 'image_2_source', 'image_3_source',
  'image_4_source', 'image_5_source', 'image_6_source', 'featured_image_source',
  'other_images_source', 'categories', 'categories_links', 'best_seller_category',
  'best_seller_link_1', 'best_seller_link_2', 'best_seller_rank_1',
  'best_seller_rank_2', 'item_weight', 'package_dimensions', 'capacity',
  'has_video', 'has_climate_pledge', 'a_plus_content', 'buybox_winner',
  'buybox_winner_link', 'has_deal', 'has_coupon', 'coupon_value',
  'variations_asins', 'offers_count'
];

// This function creates the "SheetScrape" menu in the UI.
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('SheetScrape')
    .addSubMenu(SpreadsheetApp.getUi().createMenu('Account')
      .addItem('Set API Key', 'showApiKeyPrompt')
      .addItem('View Account Info', 'showAccountInfo'))
    .addSeparator()
    .addItem('Setup/Reset Sheet', 'setupResetSheet')
    .addItem('Reset Headers to Standard', 'resetToStandardHeaders')
    .addSeparator()
    .addItem('Help & Documentation', 'showHelp')
    .addToUi();
}

// This function stores the user's API key.
function showApiKeyPrompt() {
  const ui = SpreadsheetApp.getUi();
  const result = ui.prompt(
    'SheetScrape - Set API Key',
    'Please enter your SheetScrape API key:',
    ui.ButtonSet.OK_CANCEL);

  if (result.getSelectedButton() == ui.Button.OK) {
    const apiKey = result.getResponseText().trim();
    if (apiKey) {
      // Store the key for the current user, specific to this document
      PropertiesService.getDocumentProperties().setProperty('SHEETSCRAPE_API_KEY', apiKey);
      ui.alert('✅ API Key saved successfully!');
    } else {
      ui.alert('❌ Please enter a valid API key.');
    }
  }
}

/**
 * The main SCRAPE function - scrapes web data and returns it as a spilled array
 * 
 * @param {string} url The web page URL to scrape
 * @param {range} selectors_range A horizontal range of cells containing the desired data selectors
 * @return {Array} A row of data that will spill into adjacent cells
 * @customfunction
 */
function SCRAPE(url, selectors_range) {
  // Input validation
  if (!url || !selectors_range) {
    return [["❌ Error: URL and selector range are required"]];
  }

  // Get API key from document properties
  const apiKey = PropertiesService.getDocumentProperties().getProperty('SHEETSCRAPE_API_KEY');
  if (!apiKey) {
    return [["❌ Error: API key not configured. Run Setup/Reset from menu."]];
  }

  // Convert range to array and extract non-empty selectors
  let selectors = [];
  if (Array.isArray(selectors_range)) {
    if (selectors_range.length === 1 && Array.isArray(selectors_range[0])) {
      // Handle 2D array (single row)
      selectors = selectors_range[0].filter(cell => cell && cell.toString().trim() !== '');
    } else {
      // Handle 1D array
      selectors = selectors_range.filter(cell => cell && cell.toString().trim() !== '');
    }
  } else {
    return [["❌ Error: Invalid selector range format"]];
  }

  if (selectors.length === 0) {
    return [["❌ Error: No valid selectors found in range"]];
  }

  // Limit selectors to prevent timeout (max 30 for full coverage of standard headers)
  if (selectors.length > 30) {
    console.warn(`Too many selectors (${selectors.length}), limiting to first 30 to prevent timeout`);
    selectors = selectors.slice(0, 30);
  }

  try {
    // Make the API request with aggressive timeout settings
    const response = UrlFetchApp.fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey
      },
      payload: JSON.stringify({
        url: url,
        selectors: selectors,
        marketplace: 'Amazon.com'
      }),
      muteHttpExceptions: true,
      timeout: 25000  // 25 seconds max (leave 5 seconds buffer for processing)
    });
    
    if (response.getResponseCode() !== 200) {
      const errorText = response.getContentText();
      console.error('API Error:', response.getResponseCode(), errorText);
      return [["❌ API Error: " + response.getResponseCode()]];
    }
    
    const data = JSON.parse(response.getContentText());
    
    if (!data.data || !Array.isArray(data.data) || data.data.length === 0) {
      console.error('Invalid API response format:', data);
      return [["❌ Invalid response from API"]];
    }
    
    // Return the data array for spilling
    return data.data;
    
  } catch (error) {
    console.error('SCRAPE function error:', error);
    
    // Return specific error messages based on error type
    const errorMsg = error.message || error.toString();
    if (errorMsg.includes('timeout') || errorMsg.includes('Timeout')) {
      return [['❌ TIMEOUT - API took too long (>25s). Try fewer selectors.']];
    } else if (errorMsg.includes('DNS')) {
      return [['❌ CONNECTION - Cannot reach API server']];
    } else if (errorMsg.includes('exceeded maximum execution time')) {
      return [['❌ SHEETS_TIMEOUT - Function exceeded 30s limit']];
    } else {
      return [['❌ ERROR: ' + (errorMsg.length > 50 ? errorMsg.substring(0, 50) + '...' : errorMsg)]];
    }
  }
}

/**
 * Fast scraping function with essential selectors only (optimized for 30-second limit)
 * Returns data in STANDARD_HEADERS order: Title -> BP1-5, Description, Image 1 (8 fields)
 * 
 * @param {string} url - The URL to scrape
 * @return {Array} Array of scraped data for essential fields only
 * @customfunction
 */
function SCRAPE_BASIC(url) {
  // Get the essential data using SCRAPE
  const basicSelectors = ['title', 'bullet_point_1', 'bullet_point_2', 'bullet_point_3', 'bullet_point_4', 'bullet_point_5', 'description', 'image_1_source'];
  const result = SCRAPE(url, [basicSelectors]);
  
  if (!result || !Array.isArray(result) || result.length === 0) {
    return result; // Return error as-is
  }
  
  // Map the result to match STANDARD_HEADERS order (28 columns + 1 blank)
  const mappedResult = new Array(STANDARD_HEADERS.length).fill('');
  const data = result[0]; // SCRAPE returns array of arrays
  
  // Map each piece of data to its correct position in STANDARD_HEADERS
  const mapping = {
    0: 0,   // title -> title (position 0)
    1: 1,   // bullet_point_1 -> bullet_point_1 (position 1)
    2: 2,   // bullet_point_2 -> bullet_point_2 (position 2)
    3: 3,   // bullet_point_3 -> bullet_point_3 (position 3)
    4: 4,   // bullet_point_4 -> bullet_point_4 (position 4)
    5: 5,   // bullet_point_5 -> bullet_point_5 (position 5)
    6: 7,   // description -> description (position 7)
    7: 20   // image_1_source -> image_1_source (position 20)
  };
  
  for (let i = 0; i < data.length; i++) {
    if (mapping[i] !== undefined) {
      mappedResult[mapping[i]] = data[i];
    }
  }
  
  return [mappedResult];
}

/**
 * Medium scraping function with important selectors (optimized for 30-second limit)
 * Returns data in STANDARD_HEADERS order: Title, BP1-6, Description, Image 1-5 (13 fields)
 * 
 * @param {string} url - The URL to scrape
 * @return {Array} Array of scraped data for important fields
 * @customfunction
 */
function SCRAPE_MEDIUM(url) {
  // Get the medium data using SCRAPE
  const mediumSelectors = [
    'title', 'bullet_point_1', 'bullet_point_2', 'bullet_point_3', 'bullet_point_4', 'bullet_point_5', 'bullet_point_6',
    'description', 'image_1_source', 'image_2_source', 'image_3_source', 'image_4_source', 'image_5_source'
  ];
  const result = SCRAPE(url, [mediumSelectors]);
  
  if (!result || !Array.isArray(result) || result.length === 0) {
    return result; // Return error as-is
  }
  
  // Map the result to match STANDARD_HEADERS order (28 columns + 1 blank)
  const mappedResult = new Array(STANDARD_HEADERS.length).fill('');
  const data = result[0]; // SCRAPE returns array of arrays
  
  // Map each piece of data to its correct position in STANDARD_HEADERS
  const mapping = {
    0: 0,   // title -> title (position 0)
    1: 1,   // bullet_point_1 -> bullet_point_1 (position 1)
    2: 2,   // bullet_point_2 -> bullet_point_2 (position 2)
    3: 3,   // bullet_point_3 -> bullet_point_3 (position 3)
    4: 4,   // bullet_point_4 -> bullet_point_4 (position 4)
    5: 5,   // bullet_point_5 -> bullet_point_5 (position 5)
    6: 6,   // bullet_point_6 -> bullet_point_6 (position 6)
    7: 7,   // description -> description (position 7)
    8: 20,  // image_1_source -> image_1_source (position 20)
    9: 21,  // image_2_source -> image_2_source (position 21)
    10: 22, // image_3_source -> image_3_source (position 22)
    11: 23, // image_4_source -> image_4_source (position 23)
    12: 24  // image_5_source -> image_5_source (position 24)
  };
  
  for (let i = 0; i < data.length; i++) {
    if (mapping[i] !== undefined) {
      mappedResult[mapping[i]] = data[i];
    }
  }
  
  return [mappedResult];
}
```

4. Save the script (click the floppy disk icon or Cmd/Ctrl + S). You may be asked to grant permissions the first time you run a function.

## Part 3: End-to-End Testing

Let's test the entire flow.

1. **Start your backend**: Make sure your uvicorn server is running in the terminal.

2. **Setup the Sheet**:
   - Go back to your Google Sheet. Reload the page to make the "SheetScrape" menu appear
   - Click SheetScrape > Account > Set API Key. Enter the key you defined in your `.env` file (`your-super-secret-key-123`)
   - Click SheetScrape > Setup/Reset Sheet to automatically create the ideal layout

3. **The sheet is now set up with**:
   - B2: Amazon marketplace dropdown (defaults to amazon.com)
   - A4: "ASINs" header, B4: "URLs" header, C4: "image" header
   - D4-AE4: All available selector dropdowns with defaults (title, bullet_point_1, etc.)
   - A5: Sample ASIN `B0CRDCXRK2`
   - B5: Dynamic URL formula using the marketplace from B2

4. **Run the Formula**:
   - In cell D5, the setup automatically creates: `=SCRAPE_BASIC(B5)`
   - Press Enter. After a "Loading..." message, you should see comprehensive product data spill across all columns
   - Try `=SCRAPE_MEDIUM(B5)` for more data points
   - Try `=SCRAPE(B5, D$4:AE$4)` for custom selection

Success! You have a working prototype with 70+ data points. You can add more ASINs in column A and drag the formulas down to process them all.

## Part 4: Next Steps for Production

This prototype is a great start. To make it a robust product, you need to:

1. **Deploy the Backend**: Your API needs to be running on a server, not just your local machine. Deploy it to a service like Render, Google Cloud Run, AWS Lambda, or Heroku. Remember to update the `API_URL` in your Apps Script.

2. **Implement Real Authentication**: The single API key is not secure or scalable. You need a proper user database (e.g., PostgreSQL), signup/login flows, and unique API keys for each user.

3. **Add Caching**: The current implementation includes Redis caching for improved speed and reduced redundant scrapes.

4. **Integrate Proxies**: To avoid getting blocked by sites like Amazon, use a rotating proxy service (e.g., Bright Data, Oxylabs).

5. **Build a Proper UI**: For a polished add-on, use the Apps Script HtmlService to create a sidebar for login, account management, and help documentation.

6. **Publish to Marketplace**: Submit your add-on to the Google Workspace Marketplace for wider distribution.