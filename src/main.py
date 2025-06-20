"""
SheetScrape Backend API

This is the main FastAPI application file that handles the web scraping requests
from the Google Apps Script frontend.

Updated to use Axesso API instead of web scraping to avoid bot detection.
"""

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
from src.utils.axesso import AxessoClient, AxessoError, map_axesso_to_selectors

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
else:
    logger.warning("REDIS_URL not found in environment. Caching disabled.")

# Initialize Axesso client
try:
    axesso_client = AxessoClient()
    logger.info("Axesso API client initialized successfully")
except AxessoError as e:
    logger.error(f"Failed to initialize Axesso client: {e}")
    axesso_client = None

# --- Models for API Data Structure ---
class ScrapeRequest(BaseModel):
    url: str
    selectors: List[str]
    marketplace: str = Field(default="Amazon.com", description="The marketplace to scrape from")
    force_refresh: bool = Field(default=False, description="Force a fresh scrape instead of using cache")

class CacheStats(BaseModel):
    hits: int
    misses: int
    size: int
    uptime: str

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
    description="An API to scrape web data for the SheetScrape Google Sheets Add-on using Axesso API.",
    version="1.1.0",
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
    return {
        "status": "online", 
        "message": "SheetScrape API is running with Axesso integration",
        "version": "1.1.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint with Axesso API status"""
    axesso_status = "enabled" if axesso_client else "disabled"
    return {
        "status": "healthy",
        "version": "1.1.0",
        "timestamp": time.time(),
        "axesso_api": axesso_status,
        "caching": "enabled" if redis_client else "disabled"
    }

@app.get("/cache/stats", dependencies=[Depends(verify_api_key)])
async def cache_stats():
    """Get cache statistics"""
    if not redis_client:
        raise HTTPException(status_code=404, detail="Caching not enabled")
    
    try:
        info = redis_client.info()
        stats = CacheStats(
            hits=info.get('keyspace_hits', 0),
            misses=info.get('keyspace_misses', 0),
            size=info.get('used_memory_human', 'unknown'),
            uptime=f"{info.get('uptime_in_days', 0)} days"
        )
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cache stats: {e}")

@app.post("/cache/clear", dependencies=[Depends(verify_api_key)])
async def clear_cache():
    """Clear the entire cache"""
    if not redis_client:
        raise HTTPException(status_code=404, detail="Caching not enabled")
    
    try:
        redis_client.flushall()
        return {"status": "success", "message": "Cache cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {e}")

def is_amazon_url(url: str) -> bool:
    """Check if the URL is an Amazon product URL"""
    amazon_domains = [
        'amazon.com', 'amazon.ca', 'amazon.com.mx', 'amazon.com.br',
        'amazon.co.uk', 'amazon.fr', 'amazon.de', 'amazon.nl',
        'amazon.es', 'amazon.it', 'amazon.com.tr', 'amazon.in',
        'amazon.sa', 'amazon.ae', 'amazon.eg', 'amazon.co.jp',
        'amazon.com.au', 'amazon.sg'
    ]
    
    url_lower = url.lower()
    return any(domain in url_lower for domain in amazon_domains)

@app.post("/scrape", dependencies=[Depends(verify_api_key)])
async def scrape_url(request: ScrapeRequest):
    """
    Receives a URL and a list of selectors, gets the data using Axesso API, and returns the results.
    
    If Redis is configured, results are cached for 6 hours unless force_refresh is True.
    """
    url = request.url
    selectors = request.selectors
    marketplace = request.marketplace
    force_refresh = request.force_refresh
    
    logger.info(f"Processing request for URL: {url} in marketplace: {marketplace}")
    logger.info(f"Requested selectors: {selectors}")
    
    # Check if Axesso client is available
    if not axesso_client:
        logger.error("Axesso API client not available")
        raise HTTPException(status_code=500, detail="Axesso API client not configured. Please check AXESSO_API_KEY.")
    
    # Validate that this is an Amazon URL
    if not is_amazon_url(url):
        logger.error(f"Non-Amazon URL provided: {url}")
        raise HTTPException(status_code=400, detail="Only Amazon product URLs are supported")
    
    # Check for cached result if Redis is available
    if redis_client and not force_refresh:
        cache_key = f"sheetscrape:axesso:{url}:{','.join(selectors)}:{marketplace}"
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.info(f"Returning cached data for {url}")
            try:
                cached_result = json.loads(cached_data)
                return {"data": cached_result}
            except json.JSONDecodeError:
                logger.warning("Failed to parse cached data, proceeding with fresh API call")
    
    # Get product data from Axesso API
    try:
        logger.info(f"Making Axesso API call for {url}")
        axesso_data = axesso_client.get_product_data(url)
        logger.info(f"Successfully retrieved Axesso data for ASIN: {axesso_data.get('asin', 'Unknown')}")
    except AxessoError as e:
        logger.error(f"Axesso API error for {url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Axesso API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error calling Axesso API for {url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"API call failed: {str(e)}")
    
    # Map Axesso data to the requested selectors
    try:
        logger.info(f"Mapping Axesso data to {len(selectors)} requested selectors")
        extracted_data = map_axesso_to_selectors(axesso_data, selectors)
        logger.info(f"Successfully mapped data: {[item[:50] + '...' if len(str(item)) > 50 else item for item in extracted_data]}")
    except Exception as e:
        logger.error(f"Error mapping Axesso data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Data mapping failed: {str(e)}")
    
    # Prepare response data as a 2D array for Google Sheets spilling
    response_data = [extracted_data]
    
    # Cache the result if Redis is available (cache for 6 hours)
    if redis_client:
        try:
            cache_key = f"sheetscrape:axesso:{url}:{','.join(selectors)}:{marketplace}"
            redis_client.setex(cache_key, 21600, json.dumps(response_data))  # 6 hours cache
            logger.info(f"Cached result for {url}")
        except Exception as e:
            logger.warning(f"Failed to cache result: {str(e)}")
    
    logger.info(f"Returning response: {{'data': {[item[:30] + '...' if len(str(item)) > 30 else item for item in response_data[0]]}}}")
    return {"data": response_data}

@app.get("/test-axesso", dependencies=[Depends(verify_api_key)])
async def test_axesso():
    """Test endpoint to verify Axesso API integration"""
    if not axesso_client:
        raise HTTPException(status_code=500, detail="Axesso API client not configured")
    
    # Test with a known working ASIN
    test_url = "https://amazon.com/dp/B0CRDCXRK2"
    test_selectors = ["title", "sale_price", "rating", "asin"]
    
    try:
        axesso_data = axesso_client.get_product_data(test_url)
        mapped_data = map_axesso_to_selectors(axesso_data, test_selectors)
        
        return {
            "status": "success",
            "test_url": test_url,
            "test_selectors": test_selectors,
            "mapped_data": dict(zip(test_selectors, mapped_data)),
            "raw_asin": axesso_data.get('asin'),
            "raw_title": axesso_data.get('productTitle', '')[:100] + "..."
        }
    except Exception as e:
        logger.error(f"Axesso test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Axesso test failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 