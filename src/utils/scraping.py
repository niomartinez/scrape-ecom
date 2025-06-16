"""
Scraping Utilities Module

This module contains helper functions for web scraping,
including different methods like BeautifulSoup and Playwright.
"""

import logging
import re
import time
from typing import Dict, List, Optional, Union, Any

import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, ElementHandle
import urllib.parse
import asyncio

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScrapingError(Exception):
    """Custom exception for scraping errors"""
    pass


def simple_scrape(url: str, headers: Optional[Dict[str, str]] = None) -> BeautifulSoup:
    """
    Basic scraping function using requests and BeautifulSoup
    
    Args:
        url: URL to scrape
        headers: Optional custom headers for the request
        
    Returns:
        BeautifulSoup object for the page HTML
        
    Raises:
        ScrapingError: If scraping fails
    """
    try:
        if not headers:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except requests.RequestException as e:
        logger.error(f"Request failed for URL {url}: {e}")
        raise ScrapingError(f"Failed to fetch URL: {e}")
    except Exception as e:
        logger.error(f"Scraping failed for URL {url}: {e}")
        raise ScrapingError(f"Scraping error: {e}")


async def advanced_scrape(url: str, wait_for_selector: str = 'body', timeout: int = 30000) -> str:
    """
    Advanced scraping function using Playwright with headless browser
    
    Args:
        url: URL to scrape
        wait_for_selector: CSS selector to wait for before considering page loaded
        timeout: Timeout in milliseconds
        
    Returns:
        HTML content of the page
        
    Raises:
        ScrapingError: If scraping fails
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/91.0.4472.124 Safari/537.36"
            )
            page = await context.new_page()
            
            # Navigate to URL with a more lenient loading strategy
            try:
                # First try with networkidle but with a shorter timeout
                await page.goto(url, wait_until="networkidle", timeout=15000)
            except Exception as e:
                logger.warning(f"networkidle timeout, falling back to domcontentloaded: {e}")
                # If that fails, try with domcontentloaded
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            
            # Try to wait for the selector, but continue if it times out
            try:
                await page.wait_for_selector(wait_for_selector, timeout=10000)
            except Exception as e:
                logger.warning(f"Selector wait timed out, continuing anyway: {e}")
            
            # Add a small delay for dynamic content
            await asyncio.sleep(2)
            
            # Scroll to load lazy content
            try:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                await asyncio.sleep(1)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"Scrolling error, continuing anyway: {e}")
            
            # Get HTML content
            content = await page.content()
            await browser.close()
            
            return content
    except Exception as e:
        logger.error(f"Advanced scraping failed for URL {url}: {e}")
        raise ScrapingError(f"Advanced scraping error: {e}")


def extract_data_from_selectors(html_content: str, selectors: Dict[str, str]) -> Dict[str, str]:
    """
    Extract data from HTML content based on a dictionary of selectors
    
    Args:
        html_content: HTML content to extract data from
        selectors: Dictionary mapping data keys to CSS/XPath selectors
        
    Returns:
        Dictionary of extracted data
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    results = {}
    
    for key, selector in selectors.items():
        try:
            # Check if we need to extract an attribute
            if '@' in selector:
                css_selector, attribute = selector.split('@')
                element = soup.select_one(css_selector)
                data = element.get(attribute, "") if element else ""
            else:
                # Otherwise, just get the text content
                element = soup.select_one(selector)
                data = element.get_text(strip=True) if element else ""
            
            results[key] = data
        except Exception as e:
            logger.warning(f"Failed to extract {key} using selector {selector}: {e}")
            results[key] = ""
    
    return results


def extract_specific_selectors(html_content: str, requested_selectors: List[str], 
                               selector_map: Dict[str, str]) -> List[str]:
    """
    Extract only specific selectors from HTML content in the requested order
    
    Args:
        html_content: HTML content to extract data from
        requested_selectors: List of selector keys to extract
        selector_map: Dictionary mapping selector keys to CSS/XPath selectors
        
    Returns:
        List of extracted data in the same order as requested_selectors
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    
    for key in requested_selectors:
        try:
            selector = selector_map.get(key)
            
            if not selector:
                # If selector not found in the map
                results.append(f"N/A: Unknown selector '{key}'")
                continue
            
            # Handle comma-separated selectors as fallbacks
            if ',' in selector:
                # Try each selector in order until one works
                for single_selector in selector.split(','):
                    single_selector = single_selector.strip()
                    
                    # Check if we need to extract an attribute
                    if '@' in single_selector:
                        css_selector, attribute = single_selector.split('@')
                        element = soup.select_one(css_selector)
                        if element and element.get(attribute):
                            results.append(element.get(attribute, ""))
                            break
                    else:
                        # Otherwise, just get the text content
                        element = soup.select_one(single_selector)
                        if element and element.get_text(strip=True):
                            results.append(element.get_text(strip=True))
                            break
                else:
                    # If we tried all selectors and none worked
                    results.append("")
            else:
                # Handle single selector (no comma)
                if '@' in selector:
                    css_selector, attribute = selector.split('@')
                    element = soup.select_one(css_selector)
                    data = element.get(attribute, "") if element else ""
                else:
                    # Otherwise, just get the text content
                    element = soup.select_one(selector)
                    data = element.get_text(strip=True) if element else ""
                
                results.append(data)
        except Exception as e:
            logger.warning(f"Failed to extract {key}: {e}")
            results.append("")
    
    return results


def is_javascript_heavy(url: str) -> bool:
    """
    Check if the URL is likely to require JavaScript for rendering
    
    Args:
        url: URL to check
        
    Returns:
        Boolean indicating if JavaScript is likely needed
    """
    # Check for common domains known to rely heavily on JavaScript
    js_heavy_domains = ['amazon', 'walmart', 'ebay', 'homedepot', 'target', 'bestbuy']
    parsed_url = urllib.parse.urlparse(url)
    domain = parsed_url.netloc.lower()
    
    # Check if domain contains any of the js_heavy_domains
    for js_domain in js_heavy_domains:
        if js_domain in domain:
            return True
    
    return False


async def choose_scraping_method(url: str) -> str:
    """
    Choose the appropriate scraping method based on the URL
    
    Args:
        url: URL to scrape
        
    Returns:
        HTML content of the page
    """
    if is_javascript_heavy(url):
        logger.info(f"Using advanced Playwright scraping for {url}")
        return await advanced_scrape(url)
    else:
        logger.info(f"Using simple requests scraping for {url}")
        soup = simple_scrape(url)
        return str(soup) 