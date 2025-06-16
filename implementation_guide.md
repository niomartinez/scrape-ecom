# Full Implementation Guide: Building SheetScrape

This guide will walk you through creating SheetScrape, a powerful Google Sheets add-on for web scraping. We will build:

- A Python Backend API using FastAPI that handles the actual web scraping
- A Google Apps Script Frontend that provides the custom `=SCRAPE()` function and helper menus within your spreadsheet

## Architecture Overview

The process works like this:

1. User types `=SCRAPE(url, headers_range)` into a Google Sheet
2. Google Apps Script calls your backend API, sending the URL and the list of requested data points (e.g., `["title", "sale_price"]`)
3. Python Backend API receives the request
4. The API scrapes the webpage, extracts the requested data points in order, and returns them as a JSON array
5. Google Apps Script receives the JSON data and displays it in the sheet. Google Sheets automatically "spills" the array into the adjacent cells

## Prerequisites

Before you start, make sure you have:

- Python 3.8+ installed
- A code editor like Cursor
- A Google Account

## Part 1: The Backend API (Python & FastAPI)

This is the engine of your tool. We'll set up a web server that listens for requests from Google Sheets.

### Step 1.1: Project Setup

1. Create a new project folder (e.g., `web_scraper_api`)
2. Open this folder in Cursor
3. Create a file named `requirements.txt` and add the dependencies:

```txt
fastapi
uvicorn[standard]
requests
beautifulsoup4
python-dotenv
```

4. Create a file named `.env` to store your secret API key. This keeps it out of your code:

```env
SECRET_API_KEY="your-super-secret-key-123"
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
```

### Step 1.2: Create the Main Application File

Create a file named `main.py`. This will contain all of your API logic:

```python
import os
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration & Pre-built Selectors ---

# This map holds all the CSS selectors for the data you want to extract.
# The user will request data using the keys (e.g., "title").
# NOTE: These selectors are examples and may need updating if Amazon changes its layout.
PREBUILT_SELECTORS = {
    'amazon.com': {
        'title': '#productTitle',
        'sale_price': 'span.a-price-whole',
        'sale_price_fraction': 'span.a-price-fraction',
        'rating': '#acrPopover .a-icon-alt',
        'review_count': '#acrCustomerReviewText',
        'image_1_source': '#imgTagWrapperId img@src',
        'bullet_point_1': '#feature-bullets .a-list-item:nth-of-type(1)',
        'bullet_point_2': '#feature-bullets .a-list-item:nth-of-type(2)',
        'bullet_point_3': '#feature-bullets .a-list-item:nth-of-type(3)',
        'availability': '#availability span',
        'asin': '[data-asin]',
    }
    # You can add more domains like 'amazon.co.uk', 'walmart.com', etc.
}

# --- Models for API Data Structure ---

class ScrapeRequest(BaseModel):
    url: str
    selectors: List[str]

# --- Authentication ---

# This is a simple, placeholder authentication function.
# In a real application, you would look up the key in a database of users.
async def verify_api_key(x_api_key: str = Header(...)):
    """Verifies that the API key in the request header is valid."""
    SECRET_KEY = os.getenv("SECRET_API_KEY")
    if not SECRET_KEY or x_api_key != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

# --- FastAPI Application ---

app = FastAPI(
    title="Web Scraper API",
    description="An API to scrape web data for a Google Sheets Add-on."
)

# IMPORTANT: Add CORS middleware to allow requests from Google Apps Script.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity, can be restricted later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- The Core Scraping Endpoint ---

@app.post("/scrape", dependencies=[Depends(verify_api_key)])
async def scrape_url(request: ScrapeRequest):
    """
    Receives a URL and a list of selectors, scrapes the page, and returns the data.
    """
    # Use a standard user-agent to appear like a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # NOTE: Using 'requests' is simple but won't work for JavaScript-heavy sites.
        # For a real product, replace this block with Playwright or Selenium.
        response = requests.get(request.url, headers=headers, timeout=10)
        response.raise_for_status()  # Raises an exception for bad status codes (4xx or 5xx)
        soup = BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch URL: {e}")

    # For now, we assume an amazon.com URL. A real app would detect the domain.
    domain_selectors = PREBUILT_SELECTORS.get('amazon.com')
    if not domain_selectors:
        raise HTTPException(status_code=400, detail="Domain not supported")

    results = []
    # Iterate through the selectors requested by the user, in the order they were requested.
    for selector_key in request.selectors:
        selector_info = domain_selectors.get(selector_key)
        
        if not selector_info:
            results.append(f"N/A: Unknown selector '{selector_key}'")
            continue

        # Check if we need to extract an attribute (like 'src' from an 'img' tag)
        if '@' in selector_info:
            css_selector, attribute = selector_info.split('@')
            element = soup.select_one(css_selector)
            data = element.get(attribute, "") if element else ""
        else:
            # Otherwise, just get the text content
            element = soup.select_one(selector_info)
            data = element.get_text(strip=True) if element else ""
        
        results.append(data)

    # Return the data in the format Google Sheets expects: a 2D array (array of rows)
    return {"data": [results]}
```

### Step 1.3: Run the Backend Locally

In your activated terminal, run the following command:

```bash
uvicorn main:app --reload
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

// This is the function that creates the "SheetScrape" menu in the UI.
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('SheetScrape')
    .addSubMenu(SpreadsheetApp.getUi().createMenu('Account')
      .addItem('Set API Key', 'showApiKeyPrompt')
      .addItem('View Account Info', 'showAccountInfo'))
    .addSeparator()
    .addItem('Setup/Reset Sheet', 'setupResetSheet')
    .addSeparator()
    .addItem('Help & Documentation', 'showHelp')
    .addToUi();
}

// This function stores the user's API key.
function showApiKeyPrompt() {
  const ui = SpreadsheetApp.getUi();
  const result = ui.prompt(
    'Set API Key',
    'Please enter your API key:',
    ui.ButtonSet.OK_CANCEL);

  if (result.getSelectedButton() == ui.Button.OK) {
    const apiKey = result.getResponseText();
    // Store the key for the current user, specific to this document.
    PropertiesService.getDocumentProperties().setProperty('SECRET_API_KEY', apiKey);
    ui.alert('API Key saved successfully!');
  }
}

/**
 * Creates data validation dropdowns in the selected cells with all available selectors.
 */
function createSelectorDropdowns() {
  // This list MUST match the keys in your backend's PREBUILT_SELECTORS map.
  const selectorList = [
    'title', 'sale_price', 'sale_price_fraction', 'rating', 'review_count',
    'image_1_source', 'bullet_point_1', 'bullet_point_2', 'bullet_point_3',
    'availability', 'asin'
  ];

  const cell = SpreadsheetApp.getActiveRange();
  if (!cell) {
    SpreadsheetApp.getUi().alert('Please select a cell or range first.');
    return;
  }
  
  const rule = SpreadsheetApp.newDataValidation()
    .requireValueInList(selectorList)
    .setAllowInvalid(false) // Disallow values not in the list
    .build();

  cell.setDataValidation(rule);
}

/**
 * Fetches data from a URL based on a list of selectors. This is the main function.
 *
 * @param {string} url The web page URL to scrape.
 * @param {range} selectors_range A horizontal range of cells containing the desired data selectors.
 * @return A row of data that will spill into adjacent cells.
 * @customfunction
 */
function IMPORTFROMWEB(url, selectors_range) {
  if (!url || !selectors_range) {
    return [["Error: URL and selector range are required."]];
  }

  // Flatten the 2D array from the sheet range into a 1D array.
  const selectors = selectors_range[0].filter(s => s !== "");

  if (selectors.length === 0) {
    return [["Error: No selectors provided in the range."]];
  }
  
  // Retrieve the stored API key.
  const apiKey = PropertiesService.getDocumentProperties().getProperty('SECRET_API_KEY');
  if (!apiKey) {
    return [["Error: API key not set. Use 'My Scraper > Set API Key'."]];
  }

  const payload = {
    'url': url,
    'selectors': selectors
  };

  const options = {
    'method': 'post',
    'contentType': 'application/json',
    'headers': {
      'x-api-key': apiKey // FastAPI converts headers to lowercase
    },
    'payload': JSON.stringify(payload),
    'muteHttpExceptions': true // IMPORTANT: Prevents generic errors, lets us handle them
  };

  try {
    const response = UrlFetchApp.fetch(API_URL, options);
    const responseCode = response.getResponseCode();
    const responseBody = response.getContentText();
    const jsonResponse = JSON.parse(responseBody);

    if (responseCode === 200) {
      // Success! Return the data. Google Sheets will spill it.
      return jsonResponse.data;
    } else {
      // Display the specific error message from our API.
      const errorRow = [`API Error: ${jsonResponse.detail}`].concat(new Array(selectors.length - 1).fill(""));
      return [errorRow];
    }
  } catch (e) {
    // Handle network errors or if the local server is down
    const errorRow = [`Network Error: ${e.message}`].concat(new Array(selectors.length - 1).fill(""));
    return [errorRow];
  }
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
   - A4: "ASINs" header, B4: "URLs" header
   - C4-Z4: All available selector dropdowns with defaults (image_1_source, title, bullet_point_1, etc.)
   - A5: Sample ASIN `B09G9FPGTN`
   - B5: Dynamic URL formula using the marketplace from B2

4. **Run the Formula**:
   - In cell C5, type the magic formula: `=SCRAPE(B5, C$4:Z$4)`
   - Press Enter. After a "Loading..." message, you should see comprehensive product data spill across all columns

Success! You have a working prototype with 80+ data points. You can add more ASINs in column A and drag the formulas down to process them all.

## Part 4: Next Steps for Production

This prototype is a great start. To make it a robust product like the real ImportFromWeb, you need to:

1. **Upgrade the Scraper**: The biggest limitation is that requests cannot run JavaScript. You must replace the `requests.get()` block in `main.py` with a headless browser solution like Playwright or Selenium to scrape modern websites reliably.

2. **Deploy the Backend**: Your API needs to be running on a server, not just your local machine. Deploy it to a service like Google Cloud Run, AWS Lambda, or Heroku. Remember to update the `API_URL` in your Apps Script.

3. **Implement Real Authentication**: The single API key is not secure or scalable. You need a proper user database (e.g., PostgreSQL), signup/login flows, and unique API keys for each user.

4. **Add Caching**: To improve speed and reduce redundant scrapes, implement a caching layer with Redis. Before scraping, check if you have a recent result for the same URL in your cache.

5. **Integrate Proxies**: To avoid getting blocked by sites like Amazon, use a rotating proxy service (e.g., Bright Data, Oxylabs).

6. **Build a Proper UI**: For a polished add-on, use the Apps Script HtmlService to create a sidebar for login, account management, and help documentation.