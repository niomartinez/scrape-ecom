"""
Axesso API Integration Module

This module handles Amazon product data retrieval using the Axesso API
instead of web scraping to avoid bot detection issues.
"""

import logging
import requests
import os
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, parse_qs
import re

# Configure logger
logger = logging.getLogger(__name__)

class AxessoError(Exception):
    """Custom exception for Axesso API errors"""
    pass

class AxessoClient:
    """Client for interacting with the Axesso Amazon API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('AXESSO_API_KEY')
        if not self.api_key:
            raise AxessoError("Axesso API key not found. Set AXESSO_API_KEY environment variable.")
        
        self.base_url = "https://api.axesso.de/amz/amazon-lookup-product"
        self.headers = {
            'axesso-api-key': self.api_key,
            'Cache-Control': 'no-cache',
            'User-Agent': 'SheetScrape/1.0'
        }
    
    def get_product_data(self, url: str) -> Dict[str, Any]:
        """
        Get Amazon product data from Axesso API
        
        Args:
            url: Amazon product URL
            
        Returns:
            Dictionary containing product data from Axesso API
            
        Raises:
            AxessoError: If API request fails
        """
        try:
            # Clean up the URL - ensure it has ?psc=1 for correct variation
            cleaned_url = self._clean_amazon_url(url)
            
            params = {'url': cleaned_url}
            
            logger.info(f"Making Axesso API request for URL: {cleaned_url}")
            
            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Check if product was found
            if data.get('responseStatus') != 'PRODUCT_FOUND_RESPONSE':
                error_msg = data.get('responseMessage', 'Product not found')
                raise AxessoError(f"Product not found: {error_msg}")
            
            logger.info(f"Successfully retrieved product data for ASIN: {data.get('asin', 'Unknown')}")
            return data
            
        except requests.RequestException as e:
            logger.error(f"Axesso API request failed: {e}")
            raise AxessoError(f"API request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in Axesso API call: {e}")
            raise AxessoError(f"Unexpected error: {e}")
    
    def _clean_amazon_url(self, url: str) -> str:
        """Clean and optimize Amazon URL for Axesso API"""
        # Add ?psc=1 if not present to ensure correct variation
        if '?psc=1' not in url and '&psc=1' not in url:
            separator = '&' if '?' in url else '?'
            url = f"{url}{separator}psc=1"
        
        return url

def map_axesso_to_selectors(axesso_data: Dict[str, Any], requested_selectors: List[str]) -> List[str]:
    """
    Map Axesso API response data to the SheetScrape selector format
    
    Args:
        axesso_data: Raw response data from Axesso API
        requested_selectors: List of selector keys requested by the client
        
    Returns:
        List of extracted data in the same order as requested_selectors
    """
    results = []
    
    # Define mapping from SheetScrape selectors to Axesso response fields
    selector_mapping = {
        # Basic Product Information
        'title': lambda data: data.get('productTitle', ''),
        'asin': lambda data: data.get('asin', ''),
        'url': lambda data: f"https://amazon.com/dp/{data.get('asin', '')}" if data.get('asin') else '',
        
        # Price Information
        'sale_price': lambda data: f"${data.get('price', 0):.2f}" if data.get('price') else '',
        'list_price': lambda data: f"${data.get('retailPrice', 0):.2f}" if data.get('retailPrice') and data.get('retailPrice') > 0 else '',
        'sale_price_per_unit': lambda data: '',  # Not available in Axesso
        
        # Rating and Reviews
        'rating': lambda data: data.get('productRating', ''),
        'review_count': lambda data: str(data.get('countReview', 0)) if data.get('countReview') else '',
        'times_evaluated': lambda data: str(data.get('countReview', 0)) if data.get('countReview') else '',
        
        # Availability
        'availability': lambda data: data.get('warehouseAvailability', ''),
        'ships_from': lambda data: data.get('fulfilledBy', ''),
        
        # Product Details
        'brand_name': lambda data: _extract_brand_from_details(data),
        'manufacturer': lambda data: data.get('manufacturer', ''),
        'model': lambda data: _extract_from_product_details(data, 'Item model number'),
        'color_name': lambda data: _extract_from_product_details(data, 'Color'),
        'style_name': lambda data: _extract_variation_name(data),
        'country_of_origin': lambda data: '',  # Not available in Axesso
        
        # Description and Bullet Points
        'description': lambda data: data.get('productDescription', ''),
        'bullet_points': lambda data: '\n'.join(data.get('features', [])),
        'bullet_point_1': lambda data: data.get('features', [''])[0] if data.get('features') else '',
        'bullet_point_2': lambda data: data.get('features', ['', ''])[1] if len(data.get('features', [])) > 1 else '',
        'bullet_point_3': lambda data: data.get('features', ['', '', ''])[2] if len(data.get('features', [])) > 2 else '',
        'bullet_point_4': lambda data: data.get('features', ['', '', '', ''])[3] if len(data.get('features', [])) > 3 else '',
        'bullet_point_5': lambda data: data.get('features', ['', '', '', '', ''])[4] if len(data.get('features', [])) > 4 else '',
        'bullet_point_6': lambda data: data.get('features', ['', '', '', '', '', ''])[5] if len(data.get('features', [])) > 5 else '',
        
        # Images
        'image_1_source': lambda data: data.get('imageUrlList', [''])[0] if data.get('imageUrlList') else '',
        'image_2_source': lambda data: data.get('imageUrlList', ['', ''])[1] if len(data.get('imageUrlList', [])) > 1 else '',
        'image_3_source': lambda data: data.get('imageUrlList', ['', '', ''])[2] if len(data.get('imageUrlList', [])) > 2 else '',
        'image_4_source': lambda data: data.get('imageUrlList', ['', '', '', ''])[3] if len(data.get('imageUrlList', [])) > 3 else '',
        'image_5_source': lambda data: data.get('imageUrlList', ['', '', '', '', ''])[4] if len(data.get('imageUrlList', [])) > 4 else '',
        'image_6_source': lambda data: data.get('imageUrlList', ['', '', '', '', '', ''])[5] if len(data.get('imageUrlList', [])) > 5 else '',
        'image_7_source': lambda data: data.get('imageUrlList', ['', '', '', '', '', '', ''])[6] if len(data.get('imageUrlList', [])) > 6 else '',
        'image_8_source': lambda data: data.get('imageUrlList', ['', '', '', '', '', '', '', ''])[7] if len(data.get('imageUrlList', [])) > 7 else '',
        'image_9_source': lambda data: data.get('imageUrlList', ['', '', '', '', '', '', '', '', ''])[8] if len(data.get('imageUrlList', [])) > 8 else '',
        'featured_image_source': lambda data: data.get('mainImage', {}).get('imageUrl', ''),
        'other_images_source': lambda data: ', '.join(data.get('imageUrlList', [])),
        
        # Categories
        'categories': lambda data: ' > '.join(data.get('categories', [])),
        'categories_links': lambda data: ', '.join([cat.get('url', '') for cat in data.get('categoriesExtended', [])]),
        
        # Best Seller Information
        'best_seller_category': lambda data: _extract_best_seller_category(data),
        'best_seller_link_1': lambda data: '',  # Not available in Axesso
        'best_seller_link_2': lambda data: '',  # Not available in Axesso
        'best_seller_rank_1': lambda data: _extract_best_seller_rank(data, 0),
        'best_seller_rank_2': lambda data: _extract_best_seller_rank(data, 1),
        
        # Product Dimensions
        'item_weight': lambda data: _extract_from_product_details(data, 'Item Weight'),
        'item_weight_unit_of_measure': lambda data: _extract_weight_unit(data),
        'item_dimensions_unit': lambda data: _extract_from_product_details(data, 'Product Dimensions'),
        'item_length': lambda data: _extract_dimension(data, 'Product Dimensions', 0),
        'item_length_unit_of_measure': lambda data: 'inches',
        'item_width': lambda data: _extract_dimension(data, 'Product Dimensions', 1),
        'item_width_unit_of_measure': lambda data: 'inches',
        'item_height': lambda data: _extract_dimension(data, 'Product Dimensions', 2),
        'item_height_unit_of_measure': lambda data: 'inches',
        
        # Package Information (not available in Axesso)
        'package_dimensions': lambda data: '',
        'package_weight_unit': lambda data: '',
        'package_length': lambda data: '',
        'package_width': lambda data: '',
        'package_height': lambda data: '',
        
        # Product Features
        'capacity': lambda data: _extract_from_product_details(data, 'Flash Memory Size'),
        'has_video': lambda data: 'Yes' if data.get('videoeUrlList') else 'No',
        'has_climate_pledge': lambda data: '',  # Not available in Axesso
        
        # A+ Content (not available in Axesso)
        'a_plus_content': lambda data: '',
        
        # Detail Tables
        'details_headers': lambda data: ', '.join([detail.get('name', '') for detail in data.get('productDetails', [])]),
        'details_values': lambda data: ', '.join([detail.get('value', '') for detail in data.get('productDetails', [])]),
        'feature_headers': lambda data: ', '.join([detail.get('name', '') for detail in data.get('aboutProduct', [])]),
        'feature_values': lambda data: ', '.join([detail.get('value', '') for detail in data.get('aboutProduct', [])]),
        
        # Buy Box Information
        'buybox_winner': lambda data: data.get('soldBy', ''),
        'buybox_winner_link': lambda data: '',  # Not available in Axesso
        'buybox_quantity_max': lambda data: data.get('minimalQuantity', ''),
        
        # Pricing and Deals
        'has_deal': lambda data: 'Yes' if data.get('deal', False) else 'No',
        'has_coupon': lambda data: 'Yes' if data.get('coupon') else 'No',
        'coupon_value': lambda data: data.get('coupon', ''),
        
        # Variations
        'current_variation_header': lambda data: _get_variation_header(data),
        'variation_1_asins': lambda data: _get_variation_asins(data, 0),
        'variation_1_name': lambda data: _get_variation_name(data, 0),
        'variation_2_asins': lambda data: _get_variation_asins(data, 1),
        'variation_2_name': lambda data: _get_variation_name(data, 1),
        'variation_3_asins': lambda data: _get_variation_asins(data, 2),
        'variation_3_name': lambda data: _get_variation_name(data, 2),
        'variations_asins': lambda data: ', '.join(_get_all_variation_asins(data)),
        
        # Offer Listing
        'offers_count': lambda data: '',  # Not available in Axesso
    }
    
    for selector in requested_selectors:
        try:
            mapper = selector_mapping.get(selector)
            if mapper:
                value = mapper(axesso_data)
                results.append(str(value) if value is not None else '')
                logger.info(f"Mapped {selector}: {str(value)[:100]}..." if value else f"Mapped {selector}: (empty)")
            else:
                logger.warning(f"No mapping found for selector: {selector}")
                results.append('')
        except Exception as e:
            logger.error(f"Error mapping selector {selector}: {e}")
            results.append('')
    
    return results

# Helper functions for data extraction
def _extract_brand_from_details(data: Dict) -> str:
    """Extract brand from product details or about product"""
    # Try aboutProduct first
    for item in data.get('aboutProduct', []):
        if item.get('name', '').lower() == 'brand':
            return item.get('value', '')
    
    # Try productDetails
    for item in data.get('productDetails', []):
        if item.get('name', '').lower() == 'brand':
            return item.get('value', '')
    
    return ''

def _extract_from_product_details(data: Dict, field_name: str) -> str:
    """Extract specific field from productDetails or aboutProduct"""
    # Try productDetails first
    for item in data.get('productDetails', []):
        if field_name.lower() in item.get('name', '').lower():
            return item.get('value', '')
    
    # Try aboutProduct
    for item in data.get('aboutProduct', []):
        if field_name.lower() in item.get('name', '').lower():
            return item.get('value', '')
    
    return ''

def _extract_variation_name(data: Dict) -> str:
    """Extract the current variation name"""
    variations = data.get('variations', [])
    if variations:
        for variation in variations:
            for value in variation.get('values', []):
                if value.get('selected', False):
                    return value.get('value', '')
    return ''

def _extract_best_seller_category(data: Dict) -> str:
    """Extract best seller category from product details"""
    best_seller_text = _extract_from_product_details(data, 'Best Sellers Rank')
    if best_seller_text:
        # Extract category name from best seller rank text
        match = re.search(r'in ([^(]+)', best_seller_text)
        if match:
            return match.group(1).strip()
    return ''

def _extract_best_seller_rank(data: Dict, index: int) -> str:
    """Extract best seller rank by index"""
    best_seller_text = _extract_from_product_details(data, 'Best Sellers Rank')
    if best_seller_text:
        # Extract rank numbers
        ranks = re.findall(r'#(\d+)', best_seller_text)
        if len(ranks) > index:
            return ranks[index]
    return ''

def _extract_weight_unit(data: Dict) -> str:
    """Extract weight unit from item weight"""
    weight = _extract_from_product_details(data, 'Item Weight')
    if 'pounds' in weight.lower():
        return 'pounds'
    elif 'kg' in weight.lower():
        return 'kg'
    elif 'oz' in weight.lower():
        return 'ounces'
    return ''

def _extract_dimension(data: Dict, field_name: str, index: int) -> str:
    """Extract specific dimension from dimensions string"""
    dimensions = _extract_from_product_details(data, field_name)
    if dimensions:
        # Extract numbers from dimensions string like "13.94 x 0.89 x 10.39 inches"
        numbers = re.findall(r'(\d+\.?\d*)', dimensions)
        if len(numbers) > index:
            return numbers[index]
    return ''

def _get_variation_header(data: Dict) -> str:
    """Get variation header name"""
    variations = data.get('variations', [])
    if variations:
        return variations[0].get('variationName', '')
    return ''

def _get_variation_asins(data: Dict, variation_index: int) -> str:
    """Get ASINs for specific variation"""
    variations = data.get('variations', [])
    if len(variations) > variation_index:
        values = variations[variation_index].get('values', [])
        asins = [v.get('asin', '') for v in values if v.get('asin')]
        return ', '.join(asins)
    return ''

def _get_variation_name(data: Dict, variation_index: int) -> str:
    """Get name for specific variation"""
    variations = data.get('variations', [])
    if len(variations) > variation_index:
        return variations[variation_index].get('variationName', '')
    return ''

def _get_all_variation_asins(data: Dict) -> List[str]:
    """Get all variation ASINs"""
    all_asins = []
    for variation in data.get('variations', []):
        for value in variation.get('values', []):
            if value.get('asin'):
                all_asins.append(value.get('asin'))
    return all_asins 