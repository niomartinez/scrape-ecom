# SheetScrape Apps Script Deployment Guide

This guide walks you through deploying the SheetScrape Google Apps Script to Google Sheets.

## Quick Start (Recommended for Testing)

### Step 1: Create the Script in Google Sheets

1. **Open Google Sheets**
   - Go to [sheets.google.com](https://sheets.google.com)
   - Create a new blank spreadsheet
   - Name it "SheetScrape Test"

2. **Open Apps Script Editor**
   - Click `Extensions` → `Apps Script`
   - This opens the Apps Script editor in a new tab

3. **Add the SheetScrape Code**
   - Delete the default `myFunction()` code in `Code.gs`
   - Copy and paste the entire content from `SheetScrape.js`
   - Click `File` → `Save` (or Ctrl/Cmd + S)
   - Rename the project to "SheetScrape"

4. **Update the Manifest (Optional but Recommended)**
   - Click the gear icon ⚙️ to open project settings
   - Check "Show 'appsscript.json' manifest file in editor"
   - Click the `<>` editor icon to return to files
   - Click on `appsscript.json`
   - Replace its content with the content from our `appsscript.json` file
   - Save the file

### Step 2: Start Your Backend Server (Required for Testing)

Before testing the Google Sheets integration, ensure your backend API is running:

1. **Activate Virtual Environment**
   ```bash
   cd /path/to/scrape-ecom
   source venv/bin/activate
   ```

2. **Set Environment Variables**
   ```bash
   export SECRET_API_KEY=test_key
   ```

3. **Start the Server**
   ```bash
   python run.py
   ```

4. **Verify Server is Running**
   - Visit http://localhost:8000/health
   - Should return: `{"status":"healthy","version":"1.0.0","timestamp":...}`

### Step 3: Test the Installation

1. **Return to your Google Sheet**
   - Go back to your Google Sheets tab
   - Refresh the page (F5 or Ctrl/Cmd + R)

2. **Check for the Menu**
   - You should see a new "SheetScrape" menu in the menu bar
   - If not visible, wait a few seconds and refresh again

3. **Authorize the Script**
   - Click `SheetScrape` → `Account` → `Set API Key`
   - You'll be prompted to authorize the script
   - Click "Review permissions" → Choose your Google account
   - Click "Allow" to grant necessary permissions

### Step 4: Configure Your API Key

1. **Set Your API Key**
   - After authorization, the "Set API Key" dialog should appear
   - Enter: `test_key` (for local testing)
   - Click "OK"
   - You should see "✅ API Key saved successfully!"

2. **Verify Account Info**
   - Click `SheetScrape` → `Account` → `View Account Info`
   - Confirm your API key is set (it will be partially masked)

### Step 5: Set Up Your Sheet for Testing

1. **Use Automated Setup**
   - Click `SheetScrape` → `Setup/Reset Sheet`
   - Click "Yes" to confirm
   - This creates the ideal layout with:
     - Marketplace dropdown in B2 (defaults to amazon.com)
     - Headers in row 4 (ASINs, URLs, and selector dropdowns)
     - Sample ASIN and URL formula in row 5

2. **Verify the Setup**
   Your sheet should now look like:
   ```
   Row 2:  [Marketplace: amazon.com ▼]
   Row 4:  [ASINs] [URLs] [image_1_source ▼] [title ▼] [bullet_point_1 ▼] [sale_price ▼] ...
   Row 5:  [B09G9FPGTN] [=CONCATENATE("https://", B$2, "/dp/", A5)] [Ready for SCRAPE formula]
   ```

### Step 6: Test the SCRAPE Function

1. **Add the SCRAPE Formula**
   - Click cell C5
   - Type: `=SCRAPE(B5, C$4:Z$4)`
   - Press Enter

2. **Watch the Magic Happen**
   - The function will take 5-15 seconds to process
   - Data will automatically spill across columns C, D, E, F, etc.
   - Each column will contain data matching its header selector

3. **Expected Results**
   You should see data like:
   - C5 (image_1_source): Image URL
   - D5 (title): Product title
   - E5 (bullet_point_1): First bullet point
   - F5 (sale_price): Price
   - And so on...

### Step 7: Test with Real Amazon Product

1. **Replace Sample ASIN**
   - Change A5 from `B09G9FPGTN` to `B0DS6WTXGP` (ASUS RTX 5070 Ti)
   - The URL in B5 will automatically update

2. **Re-run the SCRAPE Function**
   - Click C5 and press Enter to refresh the formula
   - You should get fresh data for the new product

3. **Add More Products**
   - Add more ASINs in A6, A7, etc.
   - Drag the URL formula from B5 down to B6, B7, etc.
   - Drag the SCRAPE formula from C5 down to C6, C7, etc.

## Advanced Deployment (For Production)

### Publishing as a Google Workspace Add-on

1. **Prepare for Publication**
   - Ensure your backend API is deployed and accessible
   - Update the `API_URL` in `SheetScrape.js` to point to your production server
   - Test thoroughly with the production API

2. **Create Deployment**
   - In Apps Script editor, click `Deploy` → `New deployment`
   - Click the gear icon ⚙️ → Select "Editor Add-on"
   - Add deployment description: "SheetScrape - Web scraping for Google Sheets"
   - Click `Deploy`

3. **Configure Add-on Settings**
   - Go to the [Google Cloud Console](https://console.cloud.google.com)
   - Select your project (or create one)
   - Enable the Google Sheets API
   - Configure OAuth consent screen with your branding

4. **Submit for Review (Optional)**
   - For public distribution, submit to Google Workspace Marketplace
   - Follow Google's add-on review guidelines
   - Include privacy policy and terms of service

## Understanding How Data Spilling Works

### The SCRAPE Function Mechanics

When you use `=SCRAPE(B5, C$4:Z$4)`:

1. **Input Processing**:
   - Reads URL from B5: `https://amazon.com/dp/B0DS6WTXGP`
   - Reads selectors from C4:Z4: `["image_1_source", "title", "bullet_point_1", "sale_price", ...]`
   - Filters out empty cells automatically

2. **API Request**:
   ```json
   POST http://localhost:8000/scrape
   {
     "url": "https://amazon.com/dp/B0DS6WTXGP",
     "selectors": ["image_1_source", "title", "bullet_point_1", "sale_price"]
   }
   ```

3. **API Response**:
   ```json
   {
     "data": [["https://m.media-amazon.com/...", "ASUS TUF Gaming GeForce RTX...", "NVIDIA Ada Lovelace...", "$979.99"]]
   }
   ```

4. **Data Spilling**:
   - C5: "https://m.media-amazon.com/..." (image_1_source)
   - D5: "ASUS TUF Gaming GeForce RTX..." (title)
   - E5: "NVIDIA Ada Lovelace..." (bullet_point_1)
   - F5: "$979.99" (sale_price)

### Customizing Selectors

You can customize which data points to scrape by:

1. **Using Dropdown Menus**: Click any header cell (C4, D4, etc.) and select from 70+ available selectors
2. **Common Selector Combinations**:
   - **Basic Info**: `title`, `sale_price`, `rating`, `review_count`
   - **Images**: `image_1_source`, `image_2_source`, `featured_image_source`
   - **Details**: `brand_name`, `model`, `color_name`, `item_weight`
   - **Bullet Points**: `bullet_point_1`, `bullet_point_2`, `bullet_point_3`

## Troubleshooting

### Common Setup Issues

1. **"SheetScrape" menu doesn't appear**
   - Refresh the Google Sheet
   - Check that the script was saved properly
   - Verify the `onOpen()` function exists in your code

2. **Authorization errors**
   - Clear browser cache and try again
   - Make sure you're using the same Google account
   - Check that all required OAuth scopes are included in `appsscript.json`

3. **API connection errors**
   - Verify your backend API is running on localhost:8000
   - Check the `API_URL` is correct (http://localhost:8000/scrape)
   - Test the API directly with curl:
     ```bash
     curl -X POST "http://localhost:8000/scrape" \
       -H "x-api-key: test_key" \
       -H "Content-Type: application/json" \
       -d '{"url":"https://amazon.com/dp/B0DS6WTXGP","selectors":["title","sale_price"]}'
     ```

4. **Function not found errors**
   - Ensure the `SCRAPE` function has the `@customfunction` annotation
   - Check that the function name is spelled correctly
   - Try refreshing the sheet and waiting a few minutes

5. **Data not spilling correctly**
   - Ensure you're using a range for selectors (e.g., `C$4:Z$4`)
   - Check that header cells contain valid selector names
   - Verify the formula syntax: `=SCRAPE(url_cell, selector_range)`

### Backend Server Issues

1. **Server won't start**
   ```bash
   # Check if virtual environment is activated
   source venv/bin/activate
   
   # Check if all dependencies are installed
   pip install -r requirements.txt
   
   # Check if environment variables are set
   export SECRET_API_KEY=test_key
   
   # Start server with verbose logging
   python run.py
   ```

2. **Server running but API calls fail**
   - Check if port 8000 is available: `lsof -i :8000`
   - Verify the health endpoint: `curl http://localhost:8000/health`
   - Check server logs for error messages

### Development Tips

1. **Debugging**
   - Use `console.log()` statements in your code
   - Check the Apps Script execution logs: `View` → `Logs`
   - Use the `testScrapeFunction()` helper function

2. **Testing Changes**
   - After modifying code, save and refresh the Google Sheet
   - Clear any cached function results by editing and re-entering formulas
   - Test with different URLs and selectors

3. **Performance**
   - The `SCRAPE` function may take 5-15 seconds for complex pages
   - Avoid making too many simultaneous requests
   - Consider implementing rate limiting in your backend

## Security Considerations

- API keys are stored locally in each Google Sheet (not shared)
- Never share your API keys in screenshots or documentation
- Use HTTPS for all API communications in production
- Consider implementing request signing for additional security

## Next Steps

After successful deployment:

1. **Create User Documentation**
   - Write guides for your specific use cases
   - Create video tutorials showing the workflow
   - Set up a support system for users

2. **Monitor Usage**
   - Track API usage and errors
   - Monitor performance and optimize as needed
   - Gather user feedback for improvements

3. **Scale Your Backend**
   - Implement proper user management
   - Add usage analytics and billing (if applicable)
   - Optimize scraping performance and reliability 