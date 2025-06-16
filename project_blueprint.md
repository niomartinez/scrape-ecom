# Project Blueprint: SheetScrape

**Tagline:** Unlock Web Data, Directly in Your Google Sheets.

## 1. Overview

SheetScrape is a powerful Google Sheets™ add-on designed to eliminate the manual, repetitive task of copy-pasting data from the web. It integrates seamlessly into the user's workflow by providing a single, powerful custom function: `=SCRAPE()`.

At its core, SheetScrape allows users—from e-commerce analysts to market researchers—to pull structured data from any webpage directly into their spreadsheet cells. By simply providing a URL and specifying the desired data points (like 'title', 'price', or 'rating'), users can automate data collection at scale.

Our primary design philosophy is **simplicity and power**. The user never has to write a single line of code. The intuitive, formula-based approach means that anyone comfortable with standard spreadsheet functions can begin scraping complex websites in minutes.

## 2. Core Features

### Powerful Array Function
The core of our service is the `=SCRAPE()` function. Unlike built-in functions that return a single value, `=SCRAPE()` returns a full row of data that automatically "spills" into adjacent cells, populating your entire dataset from a single formula.

### Dynamic Data Selection
Users are in complete control. By setting up headers using our simple dropdown menus, they can specify exactly what data they want to pull and in what order. Change a header from 'rating' to 'review_count', and the data in that column automatically updates.

### Comprehensive Selector Library
We maintain a comprehensive library of 80+ data selectors covering every aspect of Amazon product data across all 18 Amazon marketplaces. From basic info like title and price to advanced data like dimensions, variations, seller details, and special features (deals, coupons, climate pledge). Users simply select from dropdown menus - no technical knowledge required.

### Built for Scale
The workflow is designed for efficiency. A user can set up one row and then simply drag the formula down to process hundreds or thousands of items, automating hours of work with a single click-and-drag.

### Centralised & Clean
By keeping the logic in one formula per row, sheets remain clean, easy to audit, and simple to modify. There's no need to manage complex formulas in every single cell.

## 3. The User Flow: A Step-by-Step Guide

This is how a typical user will interact with SheetScrape to pull product data from Amazon.

**Objective:** Get the Title, Sale Price, Rating, and Review Count for a list of 100 products.

### Step 1: Installation & One-Time Setup

1. **Install the Add-on:** The user installs "SheetScrape" from the Google Workspace Marketplace.
2. **Authorize:** On first use, the user authorizes the add-on to run.
3. **Set API Key:** The user navigates to the new menu item SheetScrape > Account > Set API Key and enters the unique key provided to them upon signing up. This is a one-time setup per sheet.

### Step 2: Automated Sheet Setup

1. **One-Click Setup:** The user clicks SheetScrape > Setup/Reset Sheet. This automatically creates the perfect layout with:
   - Amazon marketplace dropdown in B2 (18 supported marketplaces)
   - Headers in row 4: ASINs, URLs, and 80+ selector dropdowns
   - Sample ASIN and dynamic URL formula pre-configured

2. **Marketplace Selection:** The user can choose any Amazon marketplace from the B2 dropdown (amazon.com, amazon.co.uk, amazon.de, etc.). The URL formulas automatically adapt.

3. **Add Product List:** The user pastes their 100 ASINs starting in A5, then drags the URL formula down to generate all product URLs automatically.

The sheet now looks like this:

| A | B | C | D | E | F | G | ... |
|---|---|---|---|---|---|---|-----|
| **2** | Marketplace: | amazon.com ▾ |  |  |  |  |  |
| **4** | ASINs | URLs | image_1_source ▾ | title ▾ | bullet_point_1 ▾ | asin ▾ | ... 80+ selectors |
| **5** | B09G9FPGTN | =CONCATENATE("https://", B$2, "/dp/", A5) |  |  |  |  |  |
| **6** | B08C1K6L2C | =CONCATENATE("https://", B$2, "/dp/", A6) |  |  |  |  |  |
| **...** | ... | ... |  |  |  |  |  |

### Step 3: Executing the Scrape with a Single Formula

1. **Write the Formula:** The user clicks on cell C5 and writes the master formula:
   ```
   =SCRAPE(B5, C$4:Z$4)
   ```

2. **Understanding the Formula:**
   - `B5`: The URL of the product to scrape for this row.
   - `C$4:Z$4`: The range containing all selector headers. This tells SheetScrape what data to fetch and in what order. The `$` signs lock the row, so it doesn't change when dragged down.

### Step 4: Getting the Results at Scale

1. **Automatic Spill:** After a "Loading..." message, SheetScrape returns comprehensive product data. The image source appears in C5, title in D5, bullet points in E5, and so on across all 80+ selected data points. The data automatically spills into all adjacent cells.

2. **Scale It Up:** The user clicks the small blue square at the bottom-right of cell C5 and drags it down to the last row.

**Done.** SheetScrape now processes every row with comprehensive Amazon data from any marketplace. In minutes, all 100 rows are populated with 80+ data points per product, transforming hours of manual work into an automated, scalable solution.

## 4. Target Use Cases

- **E-commerce & Amazon Sellers:** Track competitor pricing, monitor stock levels, aggregate product details for listings, and analyze customer reviews.
- **Market Researchers:** Gather data on product trends, category leaders, and pricing strategies across different marketplaces.
- **Lead Generation:** Extract business names, addresses, and phone numbers from online directories and maps.
- **Finance Professionals:** Pull stock prices, financial metrics, and news headlines from financial websites.
- **Anyone with a Repetitive Data-Entry Task:** Automate the transfer of any public, structured data from a website into a spreadsheet.

## 5. Technical Architecture Summary

- **Frontend:** A Google Sheets Add-on built with Google Apps Script. It provides the custom function, UI menus, and handles communication with the backend via UrlFetchApp.
- **Backend:** A scalable API built with Python and FastAPI. It manages authentication, job processing, and the core scraping logic using headless browsers (Playwright) to handle modern JavaScript-driven websites.
- **Authentication:** A secure API Key model. Each user has a unique key that is passed in the header of every request. 