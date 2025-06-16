# SheetScrape - Google Apps Script

This folder contains the Google Apps Script code for the SheetScrape add-on. This script provides the custom `=SCRAPE()` function and user interface menus within Google Sheets.

## Files

- `SheetScrape.js` - Main Apps Script code containing the SCRAPE function and UI menus

## How the SCRAPE Function Works

### Data Flow Overview
1. **Input**: `=SCRAPE(url_cell, selector_range)` 
   - `url_cell`: Contains the webpage URL to scrape
   - `selector_range`: Horizontal range of cells containing data selectors (headers)

2. **Processing**: SheetScrape.js sends a POST request to your backend API with:
   ```json
   {
     "url": "https://amazon.com/dp/B0DS6WTXGP",
     "selectors": ["title", "sale_price", "rating", "review_count"]
   }
   ```

3. **Response**: Backend returns scraped data in the same order:
   ```json
   {
     "data": [["ASUS TUF Gaming GeForce RTX...", "$979.99", "4.6 out of 5 stars", "123 ratings"]]
   }
   ```

4. **Output**: Data **automatically spills** across columns to match your selectors:
   - Column D (title): "ASUS TUF Gaming GeForce RTX..."
   - Column E (sale_price): "$979.99"  
   - Column F (rating): "4.6 out of 5 stars"
   - Column G (review_count): "123 ratings"

### Example Usage in Google Sheets

**Setup (using SheetScrape > Setup/Reset Sheet):**
```
Row 2:  [Marketplace: amazon.com ▼]
Row 4:  [ASINs] [URLs] [image_1_source ▼] [title ▼] [bullet_point_1 ▼] [sale_price ▼] ...
Row 5:  [B0DS6WTXGP] [=CONCATENATE("https://", B$2, "/dp/", A5)] [=SCRAPE(B5, C$4:Z$4)]
```

**The formula `=SCRAPE(B5, C$4:Z$4)` will:**
- Read the URL from B5
- Read all selectors from C4 through Z4 (skipping empty cells)
- Return data that spills from C5 across to match the number of selectors
- Each column corresponds to its header selector in the same order

## Setup Instructions

### 1. Create a New Apps Script Project

1. Open [Google Apps Script](https://script.google.com)
2. Click "New Project"
3. Replace the default `Code.gs` content with the code from `SheetScrape.js`
4. Rename the project to "SheetScrape"

### 2. Configure the API URL

In the `SheetScrape.js` file, update the `API_URL` constant:

```javascript
// For local development/testing
const API_URL = "http://localhost:8000/scrape";

// For production (replace with your deployed API URL)
const API_URL = "https://your-api-domain.com/scrape";
```

### 3. Test the Script

1. In the Apps Script editor, select the `testScrapeFunction` function
2. Click "Run" to test (you'll need to authorize the script first)
3. Check the execution log for any errors

### 4. Deploy as a Google Sheets Add-on

#### Option A: Use in a Single Sheet (Recommended for testing)

1. Open a Google Sheet
2. Go to Extensions > Apps Script
3. Paste the code from `SheetScrape.js`
4. Save and refresh the Google Sheet
5. The "SheetScrape" menu should appear

#### Option B: Deploy as a Workspace Add-on

1. In the Apps Script editor, click "Deploy" > "New deployment"
2. Choose type: "Add-on"
3. Fill in the required information:
   - Description: "SheetScrape - Unlock Web Data, Directly in Your Google Sheets"
   - Post-install tip: "Use SheetScrape > Account > Set API Key to get started"
4. Click "Deploy"

## Features

### Automated Sheet Setup
- One-click sheet setup with ideal layout
- Amazon marketplace dropdown (18 supported marketplaces)
- Dynamic URL generation based on selected marketplace
- Pre-configured with 70+ Amazon data selectors

### Menu Structure

```
SheetScrape
├── Account
│   ├── Set API Key
│   └── View Account Info
├── Setup/Reset Sheet
└── Help & Documentation
```

### Custom Function

The main function is `=SCRAPE(url, selectors_range)`:

- `url`: The webpage URL to scrape
- `selectors_range`: A range of cells containing the data selectors (headers)

### Comprehensive Amazon Selectors
Includes 70+ selectors covering:
- Basic product info (title, price, rating, availability)
- Images and media (6 image sources, featured images)
- Product details (dimensions, weight, capacity, color)
- Seller information (brand, manufacturer, ships_from)
- Rankings and reviews (best_seller_rank, rating, times_evaluated)
- Variations and options (color_name, style_name, variations)
- Special features (deals, coupons, climate_pledge)

### Step-by-Step Usage Guide

1. **Setup Sheet**: Click SheetScrape > Setup/Reset Sheet to create the ideal layout
2. **Set API Key**: Click SheetScrape > Account > Set API Key (use "test_key" for local testing)
3. **Choose Marketplace**: Select Amazon marketplace from B2 dropdown (defaults to amazon.com)
4. **Add ASINs**: Enter ASINs in column A starting from A5
5. **Generate URLs**: Drag the URL formula in B5 down to match your ASINs
6. **Customize Selectors**: Modify the dropdown selections in row 4 as needed
7. **Scrape Data**: Use the formula `=SCRAPE(B5, C$4:Z$4)` in C5 and drag down
8. **Data Spills**: Watch as data automatically fills across columns matching your selectors

## Error Handling

The script includes comprehensive error handling for:

- Missing API key
- Invalid URLs
- Network connection issues
- API errors
- Invalid selectors

All errors are displayed with helpful ❌ prefixes and clear error messages.

## Development Notes

### Testing Functions

- `testScrapeFunction()` - Test the SCRAPE function with sample data
- `clearSheetScrapeSettings()` - Clear all stored settings (for debugging)

### Security

- API keys are stored using PropertiesService (document-specific)
- Keys are masked when displayed in the UI
- All HTTP requests include proper headers

### Performance

- The function supports array spilling for efficient data display
- Error messages are padded to match the expected column count
- Network requests include proper timeout handling

## Troubleshooting

### Common Issues

1. **"API key not set" error**
   - Solution: Use SheetScrape > Account > Set API Key
   - For local testing, use: `test_key`

2. **"Network Error" messages**
   - Check if your backend API is running on localhost:8000
   - Verify the API_URL is correct (http vs https)
   - Check your internet connection

3. **"No valid selectors provided"**
   - Ensure selector cells aren't empty
   - Use the dropdown menus to set selectors

4. **Function not available**
   - Refresh the Google Sheet
   - Check if the script is properly saved
   - Verify function permissions are granted

5. **Data not spilling correctly**
   - Ensure you're using a range for selectors (e.g., `C$4:Z$4`)
   - Check that header cells contain valid selector names
   - Verify the formula syntax: `=SCRAPE(url_cell, selector_range)`

### Local Testing Setup

1. **Start your backend server**:
   ```bash
   source venv/bin/activate
   export SECRET_API_KEY=test_key
   python run.py
   ```

2. **Verify server is running**:
   - Visit http://localhost:8000/health
   - Should return: `{"status":"healthy","version":"1.0.0","timestamp":...}`

3. **Test with curl**:
   ```bash
   curl -X POST "http://localhost:8000/scrape" \
     -H "x-api-key: test_key" \
     -H "Content-Type: application/json" \
     -d '{"url":"https://amazon.com/dp/B0DS6WTXGP","selectors":["title","sale_price"]}'
   ```

### Support

For additional help:
1. Use SheetScrape > Help & Documentation
2. Check the Apps Script execution logs
3. Verify your backend API is responding correctly 