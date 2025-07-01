// --- SheetScrape Google Apps Script ---
// This script provides the custom SCRAPE() function and UI menus for SheetScrape
// Author: SheetScrape Team
// Version: 1.0

// --- Configuration ---
const API_URL = "https://sheetscrape-api.onrender.com/scrape"; 

// Define the standard header order that matches our backend selectors (31 columns + 1 blank)
const STANDARD_HEADERS = [
  'title',
  'bullet_point_1', 
  'bullet_point_2',
  'bullet_point_3', 
  'bullet_point_4',
  'bullet_point_5',
  'bullet_points',
  'description',
  'a_plus_content',
  'availability',
  'brand_name',
  'buybox_winner',
  'buybox_winner_link', 
  'variations_asins',
  'best_seller_category',
  'best_seller_rank_1',
  'best_seller_rank_2', 
  'times_evaluated',
  'asin',
  'categories',
  'image_1_source',
  'image_2_source',
  'image_3_source',
  'image_4_source', 
  'image_5_source',
  'image_6_source',
  'image_7_source',
  'image_8_source',
  'image_9_source',
  'has_video',
  '' // 1 blank column as requested
];

// All available selectors for dropdown validation - users can change to any of these
const ALL_SELECTORS = [
  'title',
  'asin',
  'url',
  'sale_price',
  'list_price',
  'sale_price_per_unit',
  'rating',
  'review_count',
  'times_evaluated',
  'availability',
  'ships_from',
  'brand_name',
  'manufacturer',
  'model',
  'color_name',
  'style_name',
  'country_of_origin',
  'description',
  'bullet_points',
  'bullet_point_1',
  'bullet_point_2',
  'bullet_point_3',
  'bullet_point_4',
  'bullet_point_5',
  'bullet_point_6',
  'image_1_source',
  'image_2_source',
  'image_3_source',
  'image_4_source',
  'image_5_source',
  'image_6_source',
  'image_7_source',
  'image_8_source',
  'image_9_source',
  'featured_image_source',
  'other_images_source',
  'categories',
  'categories_links',
  'best_seller_category',
  'best_seller_link_1',
  'best_seller_link_2',
  'best_seller_rank_1',
  'best_seller_rank_2',
  'item_weight',
  'item_weight_unit_of_measure',
  'item_dimensions_unit',
  'item_length',
  'item_length_unit_of_measure',
  'item_width',
  'item_width_unit_of_measure',
  'item_height',
  'item_height_unit_of_measure',
  'package_dimensions',
  'package_weight_unit',
  'package_length',
  'package_width',
  'package_height',
  'capacity',
  'has_video',
  'has_climate_pledge',
  'a_plus_content',
  'details_headers',
  'details_values',
  'feature_headers',
  'feature_values',
  'buybox_winner',
  'buybox_winner_link',
  'buybox_quantity_max',
  'has_deal',
  'has_coupon',
  'coupon_value',
  'current_variation_header',
  'variation_1_asins',
  'variation_1_name',
  'variation_2_asins',
  'variation_2_name',
  'variation_3_asins',
  'variation_3_name',
  'variations_asins',
  'offers_count'
];

/**
 * Creates the SheetScrape menu in the Google Sheets UI when the sheet opens
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('SheetScrape')
    .addItem('Set API Key', 'showApiKeyPrompt')
    .addItem('View Account Info', 'showAccountInfo')
    .addItem('Setup/Reset Sheet', 'setupResetSheet')
    .addItem('Reset Headers to Standard', 'resetToStandardHeaders')
    .addSeparator()
    .addItem('Help & Documentation', 'showHelp')
    .addToUi();
}

/**
 * Creates and returns a generic card for the add-on homepage.
 * This is called when the add-on is opened from the G Suite Marketplace listing
 * or from the Add-ons menu before it has file access.
 * @param {Object} e The event object.
 * @return {Card} A card built with the CardService.
 */
function onHomepage(e) {
  console.log("onHomepage event:", JSON.stringify(e));
  return createSheetScrapeCard("Welcome to SheetScrape!", "Use the menu to get started or set your API key.");
}

/**
 * Handles the onFileScopeGranted trigger.
 * This is called after the user grants file access to the add-on for the current document.
 * @param {Object} e The event object.
 */
function onFileScopeGranted(e) {
  console.log("onFileScopeGranted event:", JSON.stringify(e));
  // Could potentially run onOpen here or a specific setup if needed after granting scope
  // For now, just log it. If onOpen is set as the sheets.homepageTrigger, it might already run.
  // Consider if initial setup specific to a new document is needed here.
  onOpen(); // Rebuild the menu now that we have file scope.
}

/**
 * Helper function to create a generic Card for the add-on.
 * @param {string} title The title for the card.
 * @param {string} message The main message for the card.
 * @return {CardService.Card}
 */
function createSheetScrapeCard(title, message) {
  return CardService.newCardBuilder()
    .setHeader(CardService.newCardHeader().setTitle(title))
    .addSection(CardService.newCardSection().addWidget(CardService.newTextParagraph().setText(message)))
    .build();
}

/**
 * Shows a prompt for the user to enter their SheetScrape API key
 */
function showApiKeyPrompt() {
  const ui = SpreadsheetApp.getUi();
  const result = ui.prompt(
    'SheetScrape - Set API Key',
    'Please enter your SheetScrape API key:',
    ui.ButtonSet.OK_CANCEL);

  if (result.getSelectedButton() == ui.Button.OK) {
    const apiKey = result.getResponseText().trim();
    if (apiKey) {
      // Store the key for the current user (available across their documents)
      PropertiesService.getUserProperties().setProperty('SHEETSCRAPE_API_KEY', apiKey);
      ui.alert('✅ API Key saved successfully! It will be available across all your spreadsheets.');
    } else {
      ui.alert('❌ Please enter a valid API key.');
    }
  }
}

/**
 * Shows basic account information
 */
function showAccountInfo() {
  const ui = SpreadsheetApp.getUi();
  const apiKey = PropertiesService.getUserProperties().getProperty('SHEETSCRAPE_API_KEY');
  
  if (apiKey) {
    const maskedKey = apiKey.length > 12 ? apiKey.substring(0, 8) + '...' + apiKey.substring(apiKey.length - 4) : 'Invalid Key Format';
    ui.alert('SheetScrape Account Info', 
             `API Key: ${maskedKey}\nStatus: Connected`, 
             ui.ButtonSet.OK);
  } else {
    ui.alert('SheetScrape Account Info', 
             'No API key set. Please use SheetScrape > Set API Key to configure your credentials.', 
             ui.ButtonSet.OK);
  }
}

/**
 * Sets up or resets the entire sheet with the ideal SheetScrape layout
 */
function setupResetSheet() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSheet();
  
  // Confirm action with user
  const response = ui.alert(
    'Setup/Reset Sheet',
    'This will clear the current sheet and set up the ideal SheetScrape layout. Continue?',
    ui.ButtonSet.YES_NO
  );
  
  if (response !== ui.Button.YES) {
    return;
  }
  
  // Clear the sheet
  sheet.clear();
  
  // Amazon marketplaces for B2 dropdown
  const amazonMarketplaces = [
    'amazon.com',
    'amazon.ca',
    'amazon.com.mx',
    'amazon.com.br',
    'amazon.co.uk',
    'amazon.fr',
    'amazon.de',
    'amazon.nl',
    'amazon.es',
    'amazon.it',
    'amazon.com.tr',
    'amazon.in',
    'amazon.sa',
    'amazon.ae',
    'amazon.eg',
    'amazon.co.jp',
    'amazon.com.au',
    'amazon.sg'
  ];
  
  // Set up B2 marketplace dropdown
  sheet.getRange('A2').setValue('Marketplace:').setFontWeight('bold');
  const marketplaceRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(amazonMarketplaces)
    .setAllowInvalid(false)
    .setHelpText('Choose Amazon marketplace')
    .build();
  sheet.getRange('B2').setDataValidation(marketplaceRule).setValue('amazon.com');
  
  // Set up row 4 headers
  sheet.getRange('A4').setValue('ASINs').setFontWeight('bold').setBackground('#f0f0f0');
  sheet.getRange('B4').setValue('URLs').setFontWeight('bold').setBackground('#f0f0f0');
  
  // Create selector dropdown rule with enhanced styling
  const selectorRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(ALL_SELECTORS)
    .setAllowInvalid(false)
    .setHelpText('Choose data point to scrape')
    .build();
  
  // Set up C4 with just "Image" by default and has the formula on C5 as =IF(image_1_source<>"", IMAGE(image_1_source), "")
  sheet.getRange('C4').setValue('image').setFontWeight('bold').setBackground('#f0f0f0');
  // image_1_source is at position 20 in STANDARD_HEADERS (0-based), so column D=4, so image_1_source = column 4+20 = column X (24)
  sheet.getRange('C5').setValue('=IF(X5<>"", IMAGE(X5), "")');
  
  // Format C4 (image header) with same card-like styling as other headers
  const imageHeaderCell = sheet.getRange('C4');
  imageHeaderCell.setHorizontalAlignment('center');
  imageHeaderCell.setVerticalAlignment('middle');
  imageHeaderCell.setBorder(true, true, true, true, true, true, '#4285F4', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
  imageHeaderCell.setBackground('#F8F9FA'); // Same card background
  imageHeaderCell.setFontColor('#1A73E8'); // Same blue text color
  imageHeaderCell.setFontSize(10); // Same font size
  sheet.setColumnWidth(3, 120); // Set image column width
  sheet.setRowHeight(4, 72); // Ensure row height is consistent
  
  // Add headers starting from column D (column 4) using STANDARD_HEADERS
  const headerRange = sheet.getRange(4, 4, 1, STANDARD_HEADERS.length);
  headerRange.setValues([STANDARD_HEADERS]);
  
  // Format headers with enhanced styling
  headerRange.setFontWeight('bold');
  headerRange.setBackground('#E8F0FE');
  headerRange.setBorder(true, true, true, true, true, true);
  headerRange.setHorizontalAlignment('center');
  headerRange.setVerticalAlignment('middle');
  
  // Set column widths for data columns (D onwards) - approximately 2.5 inches
  const startColumn = 4; // Column D
  for (let i = 0; i < STANDARD_HEADERS.length; i++) {
    sheet.setColumnWidth(startColumn + i, 180); // ~2.5 inches in pixels
  }
  
  // Set row height for header row (approximately 1 inch)
  sheet.setRowHeight(4, 72);
  
  // Freeze rows 1-4 to keep headers visible
  sheet.setFrozenRows(4);
  
  // Add data validation to header cells with enhanced dropdown styling
  for (let i = 0; i < STANDARD_HEADERS.length; i++) {
    const cell = sheet.getRange(4, 4 + i);
    cell.setDataValidation(selectorRule);
    
    // Add card-like appearance with enhanced styling
    cell.setBorder(true, true, true, true, true, true, '#4285F4', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
    cell.setBackground('#F8F9FA'); // Slightly different background for card effect
    cell.setFontColor('#1A73E8'); // Blue text color for better contrast
    cell.setFontSize(10); // Slightly smaller font for better fit
  }
  
  // Pre-format data area (rows 5 and beyond) for better text handling
  const dataStartRow = 5;
  const dataRows = 100; // Format first 100 rows for future data
  const dataRange = sheet.getRange(dataStartRow, startColumn, dataRows, STANDARD_HEADERS.length);
  
  // Set data cell formatting
  dataRange.setWrap(true); // Enable text wrapping
  dataRange.setHorizontalAlignment('left'); // Left-align text content as requested
  dataRange.setVerticalAlignment('top'); // Align to top for better readability
  
  // Set a subtle border for data cells
  dataRange.setBorder(true, true, true, true, true, true, '#E0E0E0', SpreadsheetApp.BorderStyle.SOLID_THIN);
  
  // Add some sample data and formulas
  sheet.getRange('A5').setValue('B0CRDCXRK2'); // Sample ASIN - ASUS RTX 5070 Ti (known working)
  sheet.getRange('B5').setValue('=CONCATENATE("https://", B$2, "/dp/", A5)'); // Dynamic URL formula
  
  // Add sample SCRAPE formula using the new headers
  const lastColumn = columnToLetter(4 + STANDARD_HEADERS.length - 1);
  sheet.getRange('D5').setValue(`=SCRAPE_BASIC($B5)`);
  
  // Format the sample data with enhanced styling
  sheet.getRange('A5:B5').setBorder(true, true, true, true, true, true);
  sheet.getRange('D5').setBorder(true, true, true, true, true, true);
  
  // Format A and B columns for better appearance
  sheet.getRange('A4:B4').setHorizontalAlignment('center');
  sheet.getRange('A4:B4').setVerticalAlignment('middle');
  sheet.setColumnWidth(1, 120); // ASIN column width
  sheet.setColumnWidth(2, 200); // URL column width
  
  // Add text wrapping for URL column (B5 and beyond) for better readability
  const urlDataRange = sheet.getRange(5, 2, 100, 1); // Column B, rows 5-104
  urlDataRange.setWrap(true);
  urlDataRange.setHorizontalAlignment('left');
  urlDataRange.setVerticalAlignment('top');
  
  ui.alert('✅ Success!', 'Sheet has been set up with the ideal SheetScrape layout.', ui.ButtonSet.OK);
}

/**
 * Shows help and documentation for SheetScrape
 */
function showHelp() {
  const ui = SpreadsheetApp.getUi();
  const helpText = `
🔧 SheetScrape Quick Start Guide:

1️⃣ Setup:
   • Set your API key: SheetScrape > Set API Key
   • Set up your sheet: SheetScrape > Setup/Reset Sheet

2️⃣ Usage:
   • Choose your Amazon marketplace from the B2 dropdown
   • Add ASINs in column A (starting from A5)
   • Drag the URL formula in column B down to match your ASINs
   • Customize selectors in row 4 using the dropdowns
   • Use the SCRAPE formula starting in C5
   • Drag the SCRAPE formula down to process all ASINs

3️⃣ Example Formula:
   • C5: =SCRAPE(B5, C$4:Z$4)
   • This will scrape all selected data points for each ASIN

📚 For detailed documentation, visit: sheetscrape.com/docs
  `;
  
  ui.alert('SheetScrape Help', helpText, ui.ButtonSet.OK);
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

  // Get API key from user properties
  const apiKey = PropertiesService.getUserProperties().getProperty('SHEETSCRAPE_API_KEY');
  if (!apiKey) {
    return [["❌ Error: API key not configured. Please use SheetScrape > Set API Key."]];
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

  // Limit selectors to prevent timeout (max 32 for full coverage of standard headers)
  if (selectors.length > 32) {
    console.warn(`Too many selectors (${selectors.length}), limiting to first 32 to prevent timeout`);
    selectors = selectors.slice(0, 32);
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
 * Helper function to test the SCRAPE function with sample data
 * This can be called from the Apps Script editor for debugging
 */
function testScrapeFunction() {
  const testUrl = "https://www.amazon.com/dp/B09G9FPGTN";
  const testSelectors = [["title", "sale_price", "rating"]];
  
  // For testing, you might need to temporarily set a user property if not done via UI
  // PropertiesService.getUserProperties().setProperty('SHEETSCRAPE_API_KEY', 'YOUR_TEST_API_KEY');

  const result = SCRAPE(testUrl, testSelectors);
  console.log("Test result:", result);
  return result;
}

/**
 * Utility function to clear all SheetScrape settings (for debugging)
 */
function clearSheetScrapeSettings() {
  PropertiesService.getUserProperties().deleteProperty('SHEETSCRAPE_API_KEY');
  SpreadsheetApp.getUi().alert('✅ SheetScrape user settings (API Key) cleared');
}

/**
 * Helper function to convert column index to column letter (e.g., 1 -> A, 27 -> AA)
 * @param {number} column - The 1-based column index
 * @return {string} The column letter(s)
 */
function columnToLetter(column) {
  let temp, letter = '';
  while (column > 0) {
    temp = (column - 1) % 26;
    letter = String.fromCharCode(temp + 65) + letter;
    column = (column - temp - 1) / 26;
  }
  return letter;
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
  
  // Map the result to match STANDARD_HEADERS order (31 columns + 1 blank)
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
 * Returns data in STANDARD_HEADERS order: Title, BP1-6, Description, Image 1-9 (16 fields)
 * 
 * @param {string} url - The URL to scrape
 * @return {Array} Array of scraped data for important fields
 * @customfunction
 */
function SCRAPE_MEDIUM(url) {
  // Get the medium data using SCRAPE
  const mediumSelectors = [
    'title', 'bullet_point_1', 'bullet_point_2', 'bullet_point_3', 'bullet_point_4', 'bullet_point_5', 'bullet_point_6',
    'description', 'image_1_source', 'image_2_source', 'image_3_source', 'image_4_source', 'image_5_source', 
    'image_6_source', 'image_7_source', 'image_8_source', 'image_9_source'
  ];
  const result = SCRAPE(url, [mediumSelectors]);
  
  if (!result || !Array.isArray(result) || result.length === 0) {
    return result; // Return error as-is
  }
  
  // Map the result to match STANDARD_HEADERS order (31 columns + 1 blank)
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
    6: 6,   // bullet_point_6 -> bullet_point_6 (position 6) - NEW for medium
    7: 7,   // description -> description (position 7)
    8: 20,  // image_1_source -> image_1_source (position 20)
    9: 21,  // image_2_source -> image_2_source (position 21)
    10: 22, // image_3_source -> image_3_source (position 22)
    11: 23, // image_4_source -> image_4_source (position 23)
    12: 24, // image_5_source -> image_5_source (position 24)
    13: 25, // image_6_source -> image_6_source (position 25)
    14: 26, // image_7_source -> image_7_source (position 26)
    15: 27, // image_8_source -> image_8_source (position 27)
    16: 28  // image_9_source -> image_9_source (position 28)
  };
  
  for (let i = 0; i < data.length; i++) {
    if (mapping[i] !== undefined) {
      mappedResult[mapping[i]] = data[i];
    }
  }
  
  return [mappedResult];
}

/**
 * Manually reset headers to the standard 31-column layout
 * Call this function manually if you want to reset headers after customizing them
 */
function resetToStandardHeaders() {
  const sheet = SpreadsheetApp.getActiveSheet();
  
  // Reset headers starting from column D (column 4) using STANDARD_HEADERS
  const headerRange = sheet.getRange(4, 4, 1, STANDARD_HEADERS.length);
  headerRange.setValues([STANDARD_HEADERS]);
  
  // Update the image formula to match the correct position
  sheet.getRange('C5').setValue('=IF(X5<>"", IMAGE(X5), "")');
  
  SpreadsheetApp.getUi().alert('Headers reset to standard layout!');
} 