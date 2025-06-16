// --- SheetScrape Google Apps Script ---
// This script provides the custom SCRAPE() function and UI menus for SheetScrape
// Author: SheetScrape Team
// Version: 1.0

// --- Configuration ---
// This should point to your backend API. Use your local URL for testing.
// When you deploy, change this to your live server URL.
// For Render deployment, use: https://your-service-name.onrender.com/scrape
const API_URL = "https://sheetscrape-api.onrender.com/scrape";  // Update this with your actual Render URL

/**
 * Creates the SheetScrape menu in the Google Sheets UI when the sheet opens
 */
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
      // Store the key for the current user, specific to this document
      PropertiesService.getDocumentProperties().setProperty('SHEETSCRAPE_API_KEY', apiKey);
      ui.alert('✅ API Key saved successfully!');
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
  const apiKey = PropertiesService.getDocumentProperties().getProperty('SHEETSCRAPE_API_KEY');
  
  if (apiKey) {
    const maskedKey = apiKey.substring(0, 8) + '...' + apiKey.substring(apiKey.length - 4);
    ui.alert('SheetScrape Account Info', 
             `API Key: ${maskedKey}\nStatus: Connected`, 
             ui.ButtonSet.OK);
  } else {
    ui.alert('SheetScrape Account Info', 
             'No API key set. Please use Account > Set API Key to configure your credentials.', 
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
  
  // All available selectors - must match backend exactly
  const allSelectors = [
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
  
  // Create selector dropdown rule
  const selectorRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(allSelectors)
    .setAllowInvalid(false)
    .setHelpText('Choose data point to scrape')
    .build();
  

  // Set up C4 with just "Image" by default and has the formula on C5 as =IF(AM5<>"", IMAGE(AM5), "")
  sheet.getRange('C4').setValue('image').setFontWeight('bold').setBackground('#f0f0f0');
  sheet.getRange('C5').setValue('=IF(AM5<>"", IMAGE(AM5), "")');

  
  // Set up D4 with title default
  sheet.getRange('D4').setDataValidation(selectorRule).setValue('title')
    .setFontWeight('bold').setBackground('#f0f0f0');

  // Set up D5 with formula =SCRAPE($B5, $D$4:$BZ$4)
  sheet.getRange('D5').setValue('=SCRAPE($B5, $D$4:$CA$4)');
  
  // Set up E4 with bullet_point_1 default
  sheet.getRange('E4').setDataValidation(selectorRule).setValue('bullet_point_1')
    .setFontWeight('bold').setBackground('#f0f0f0');
  
  // First, make sure the sheet has enough columns for all our selectors
  // Google Sheets default is usually 26 columns (A-Z), we need to ensure we have enough
  const totalColumnsNeeded = 6 + allSelectors.length - 3; // Starting from col F (6) + all remaining selectors
  const currentLastColumn = sheet.getLastColumn();
  
  if (currentLastColumn < totalColumnsNeeded) {
    // Add more columns if needed - we may need to insert additional columns
    const columnsToAdd = totalColumnsNeeded - currentLastColumn;
    if (columnsToAdd > 0) {
      sheet.insertColumnsAfter(currentLastColumn, columnsToAdd);
    }
  }
  
  // Use all selectors as requested
  const startColumn = 6; // Column F
  const endColumn = startColumn + allSelectors.length - 3; // Include all selectors
  
  for (let i = 0; i < allSelectors.length - 3; i++) {
    const columnIndex = startColumn + i;
    const cell = sheet.getRange(4, columnIndex);
    cell.setDataValidation(selectorRule)
      .setValue(allSelectors[i + 3]) // Skip the first 3 we already used
      .setFontWeight('bold')
      .setBackground('#f0f0f0');
  }
  
  // Add some sample data and formulas
  sheet.getRange('A5').setValue('B0CRDCXRK2'); // Sample ASIN - ASUS RTX 5070 Ti (known working)
  sheet.getRange('B5').setValue('=CONCATENATE("https://", B$2, "/dp/", A5)'); // Dynamic URL formula
  
  // // Add instructions
  // sheet.getRange('A1').setValue('SheetScrape Setup Complete! 🎉').setFontWeight('bold').setFontSize(14);
  // sheet.getRange('A6').setValue('Instructions:').setFontWeight('bold');
  // sheet.getRange('A7').setValue('1. Add more ASINs in column A (starting from A5)');
  // sheet.getRange('A8').setValue('2. Drag the URL formula in B5 down to match your ASINs');
  
  // // Calculate the column letter for the last selector column
  // const lastColumnLetter = columnToLetter(endColumn);
  // sheet.getRange('A9').setValue(`3. In C5, enter: =SCRAPE(B5, C$4:${lastColumnLetter}$4)`);
  // sheet.getRange('A10').setValue('4. Drag the SCRAPE formula down to process all your ASINs');
  
  // // Style the instructions
  // sheet.getRange('A6:A10').setFontStyle('italic').setBackground('#fff2cc');
  
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
   • Set your API key: SheetScrape > Account > Set API Key
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

  // Get API key from script properties
  const apiKey = PropertiesService.getScriptProperties().getProperty('API_KEY');
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

  // Limit selectors to prevent timeout (max 20 for speed)
  if (selectors.length > 20) {
    console.warn(`Too many selectors (${selectors.length}), limiting to first 20 to prevent timeout`);
    selectors = selectors.slice(0, 20);
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
  
  const result = SCRAPE(testUrl, testSelectors);
  console.log("Test result:", result);
  return result;
}

/**
 * Utility function to clear all SheetScrape settings (for debugging)
 */
function clearSheetScrapeSettings() {
  PropertiesService.getDocumentProperties().deleteProperty('SHEETSCRAPE_API_KEY');
  SpreadsheetApp.getUi().alert('✅ SheetScrape settings cleared');
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
 * 
 * @param {string} url - The URL to scrape
 * @return {Array} Array of scraped data for essential fields only
 * @customfunction
 */
function SCRAPE_BASIC(url) {
  // Essential selectors only (6 fields for maximum speed)
  const basicSelectors = ['title', 'sale_price', 'rating', 'review_count', 'availability', 'brand_name'];
  
  return SCRAPE(url, [basicSelectors]);
}

/**
 * Medium scraping function with important selectors (optimized for 30-second limit)
 * 
 * @param {string} url - The URL to scrape
 * @return {Array} Array of scraped data for important fields
 * @customfunction
 */
function SCRAPE_MEDIUM(url) {
  // Important selectors (15 fields - good balance of data vs speed)
  const mediumSelectors = [
    'title', 'sale_price', 'list_price', 'rating', 'review_count', 
    'availability', 'brand_name', 'manufacturer', 'model', 'description',
    'bullet_point_1', 'image_1_source', 'categories', 'asin', 'url'
  ];
  
  return SCRAPE(url, [mediumSelectors]);
} 