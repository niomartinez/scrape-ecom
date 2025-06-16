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
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
        
        # Add a small delay to avoid being too aggressive
        time.sleep(1)
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        logger.info(f"Simple scraping got {len(response.text)} characters")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except requests.RequestException as e:
        logger.error(f"Request failed for URL {url}: {e}")
        raise ScrapingError(f"Failed to fetch URL: {e}")
    except Exception as e:
        logger.error(f"Scraping failed for URL {url}: {e}")
        raise ScrapingError(f"Scraping error: {e}")


async def advanced_scrape(url: str, wait_for_selector: str = 'body', timeout: int = 20000) -> str:
    """
    Advanced scraping function using Playwright with headless browser
    Optimized for speed to work within Google Sheets 30-second custom function limit
    
    Args:
        url: URL to scrape
        wait_for_selector: CSS selector to wait for before considering page loaded
        timeout: Timeout in milliseconds (reduced to 20s for speed)
        
    Returns:
        HTML content of the page
        
    Raises:
        ScrapingError: If scraping fails
    """
    try:
        async with async_playwright() as p:
            # Use faster browser settings optimized for speed
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-field-trial-config',
                    '--disable-back-forward-cache',
                    '--disable-ipc-flooding-protection',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-default-apps',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-sync',
                    '--disable-translate',
                    '--hide-scrollbars',
                    '--mute-audio',
                    '--no-zygote',
                    '--single-process'  # Faster startup
                ]
            )
            
            # Create context with realistic settings but optimized for speed
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1280, 'height': 720},  # Smaller viewport for speed
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0'
                }
            )
            
            page = await context.new_page()
            
            # Disable images and CSS for faster loading
            await page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}", lambda route: route.abort())
            
            try:
                # Navigate with shorter timeout for speed
                await page.goto(url, wait_until='domcontentloaded', timeout=15000)
                logger.info(f"Page loaded successfully for {url}")
                
                # Quick wait for essential elements (reduced timeout)
                try:
                    await page.wait_for_selector("#productTitle, #landingImage, #feature-bullets", timeout=5000)
                except Exception:
                    logger.warning("Product elements wait timed out, continuing anyway")
                
                # Minimal scrolling for speed
                try:
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3)")
                    await page.wait_for_timeout(500)  # Reduced wait time
                except Exception:
                    pass
                
            except Exception as e:
                logger.warning(f"Page loading issues for {url}: {e}, but continuing with extraction")
            
            # Get HTML content
            html_content = await page.content()
            logger.info(f"Final HTML content length: {len(html_content)} characters")
            
            # Quick check for blocked content
            if len(html_content) < 5000:
                logger.warning(f"Suspiciously short HTML content ({len(html_content)} chars), might be blocked")
            
            await browser.close()
            return html_content
            
    except Exception as e:
        logger.error(f"Advanced scraping failed for {url}: {e}")
        raise ScrapingError(f"Playwright scraping failed: {e}")


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
    
    logger.info(f"Extracting {len(requested_selectors)} selectors from HTML content")
    
    for key in requested_selectors:
        try:
            selector = selector_map.get(key)
            
            if not selector:
                # If selector not found in the map
                logger.warning(f"Selector '{key}' not found in selector map")
                results.append(f"N/A: Unknown selector '{key}'")
                continue
            
            logger.info(f"Processing selector '{key}' with CSS: '{selector}'")
            
            # Handle comma-separated selectors as fallbacks
            if ',' in selector:
                # Try each selector in order until one works
                found_data = False
                for single_selector in selector.split(','):
                    single_selector = single_selector.strip()
                    logger.info(f"  Trying fallback selector: '{single_selector}'")
                    
                    # Check if we need to extract an attribute
                    if '@' in single_selector:
                        css_selector, attribute = single_selector.split('@')
                        element = soup.select_one(css_selector)
                        if element and element.get(attribute):
                            data = element.get(attribute, "")
                            logger.info(f"  Found data via attribute '{attribute}': '{data[:100]}...'")
                            results.append(data)
                            found_data = True
                            break
                    else:
                        # Otherwise, just get the text content
                        element = soup.select_one(single_selector)
                        if element and element.get_text(strip=True):
                            data = element.get_text(strip=True)
                            logger.info(f"  Found data via text: '{data[:100]}...'")
                            results.append(data)
                            found_data = True
                            break
                
                if not found_data:
                    # If we tried all selectors and none worked
                    logger.warning(f"  No data found for any fallback selectors for '{key}'")
                    results.append("")
            else:
                # Handle single selector (no comma)
                if '@' in selector:
                    css_selector, attribute = selector.split('@')
                    element = soup.select_one(css_selector)
                    data = element.get(attribute, "") if element else ""
                    if data:
                        logger.info(f"  Found data via attribute '{attribute}': '{data[:100]}...'")
                    else:
                        logger.warning(f"  No data found for attribute selector '{css_selector}@{attribute}'")
                else:
                    # Otherwise, just get the text content
                    element = soup.select_one(selector)
                    data = element.get_text(strip=True) if element else ""
                    if data:
                        logger.info(f"  Found data via text: '{data[:100]}...'")
                    else:
                        logger.warning(f"  No data found for text selector '{selector}'")
                
                results.append(data)
        except Exception as e:
            logger.error(f"Failed to extract {key}: {e}")
            results.append("")
    
    logger.info(f"Final extraction results: {[r[:50] + '...' if len(r) > 50 else r for r in results]}")
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
        try:
            playwright_content = await advanced_scrape(url)
            
            # If Playwright returns very little content, try simple scraping as fallback
            if len(playwright_content) < 10000:
                logger.warning(f"Playwright returned minimal content ({len(playwright_content)} chars), trying simple scraping as fallback")
                try:
                    soup = simple_scrape(url)
                    simple_content = str(soup)
                    
                    # Use whichever method returned more content
                    if len(simple_content) > len(playwright_content):
                        logger.info(f"Simple scraping returned more content ({len(simple_content)} vs {len(playwright_content)} chars), using simple method")
                        return simple_content
                    else:
                        logger.info(f"Playwright content is still better ({len(playwright_content)} vs {len(simple_content)} chars), using Playwright")
                        return playwright_content
                except Exception as e:
                    logger.warning(f"Simple scraping fallback failed: {e}, using Playwright result")
                    return playwright_content
            
            return playwright_content
        except Exception as e:
            logger.error(f"Playwright scraping failed: {e}, falling back to simple scraping")
            soup = simple_scrape(url)
            return str(soup)
    else:
        logger.info(f"Using simple requests scraping for {url}")
        soup = simple_scrape(url)
        return str(soup) 