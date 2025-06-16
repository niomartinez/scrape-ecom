"""
SheetScrape Backend API

This is the main FastAPI application file that handles the web scraping requests
from the Google Apps Script frontend.
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
else:
    logger.warning("REDIS_URL not found in environment. Caching disabled.")

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

@app.post("/scrape", dependencies=[Depends(verify_api_key)])
async def scrape_url(request: ScrapeRequest):
    """
    Receives a URL and a list of selectors, scrapes the page, and returns the data.
    
    If Redis is configured, results are cached for 24 hours unless force_refresh is True.
    """
    url = request.url
    selectors = request.selectors
    marketplace = request.marketplace
    force_refresh = request.force_refresh
    
    logger.info(f"Processing request for URL: {url} in marketplace: {marketplace}")
    logger.debug(f"Requested selectors: {selectors}")
    
    # Check for cached result if Redis is available
    if redis_client and not force_refresh:
        cache_key = f"sheetscrape:{url}:{','.join(selectors)}:{marketplace}"
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for URL: {url}")
            return json.loads(cached_data)
    
    try:
        # Choose scraping method based on URL
        html_content = await choose_scraping_method(url)
        
        # Get selectors map for this domain (currently optimized for Amazon)
        domain_selectors = get_selectors_for_domain(url, marketplace)
        
        if not domain_selectors:
            raise HTTPException(status_code=400, detail="Domain not supported")
        
        # Extract only the requested selectors in the order specified
        results = extract_specific_selectors(html_content, selectors, domain_selectors)
        
        # Format response as expected by Google Sheets
        response = {"data": [results]}
        
        # Cache the result if Redis is available
        if redis_client:
            cache_key = f"sheetscrape:{url}:{','.join(selectors)}:{marketplace}"
            # Cache for 24 hours
            redis_client.setex(cache_key, 86400, json.dumps(response))
        
        return response
    except ScrapingError as e:
        logger.error(f"Scraping error for URL {url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error processing URL {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 