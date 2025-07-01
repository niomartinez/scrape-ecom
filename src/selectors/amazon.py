"""
Amazon Selectors Module

This module contains all CSS/XPath selectors for Amazon product pages.
These selectors cover all aspects of Amazon product data including:
- Basic information (title, price, rating)
- Product details (dimensions, weight, specifications)
- Images and media sources
- Reviews and ratings
- Availability and shipping information
- Variations and options
- Best seller information
- And more
"""

# Base selectors common to all Amazon domains
AMAZON_SELECTORS = {
    # Basic Product Information
    'title': '#productTitle',
    'asin': '[data-asin]@data-asin',
    'url': 'link[rel="canonical"]@href',
    
    # Price Information
    'sale_price': '#corePriceDisplay_desktop_feature_div .a-price .a-offscreen, #corePrice_feature_div .a-price .a-offscreen, #priceblock_ourprice, .a-price .a-offscreen, #price_inside_buybox, .a-section.a-spacing-micro .a-price .a-offscreen',
    'list_price': '#corePriceDisplay_desktop_feature_div .a-price.a-text-price .a-offscreen, #corePrice_feature_div .a-price.a-text-price .a-offscreen, .a-price.a-text-price .a-offscreen, #priceblock_ourprice, #listPrice',
    'sale_price_per_unit': '.a-price-per-unit',
    
    # Rating and Reviews
    'rating': '#acrPopover .a-icon-alt',
    'review_count': '#acrCustomerReviewText',
    'times_evaluated': '#reviewsMedley .a-size-base.a-color-secondary',
    
    # Availability
    'availability': '#availability span',
    'ships_from': '#tabular-buybox-truncate-1 .tabular-buybox-text',
    
    # Product Details
    'brand_name': '#bylineInfo, .po-brand .a-span9, #productDetails_techSpec_section_1 tr:contains("Brand") td, #detailBullets_feature_div li:contains("Brand") span.a-text-bold + span',
    'manufacturer': '#poExpander .po-manufacturer .po-break-word, #productDetails_techSpec_section_1 tr:contains("Manufacturer") td, #detailBullets_feature_div li:contains("Manufacturer") span.a-text-bold + span',
    'model': '#poExpander .po-model_name .po-break-word, #productDetails_techSpec_section_1 tr:contains("Model") td, #detailBullets_feature_div li:contains("Model") span.a-text-bold + span',
    'color_name': '#variation_color_name .selection',
    'style_name': '#variation_style_name .selection',
    'country_of_origin': '#poExpander .po-country_of_origin .po-break-word',
    
    # Description and Bullet Points
    'description': '#productDescription p, #feature-bullets .a-list-item',
    'bullet_points': '#feature-bullets .a-list-item, #detailBullets_feature_div li .a-list-item, #poExpander .a-list-item',
    'bullet_point_1': '#feature-bullets .a-list-item:nth-of-type(1), #detailBulletsWrapper_feature_div li:nth-of-type(1), #poExpander .a-list-item:nth-of-type(1)',
    'bullet_point_2': '#feature-bullets .a-list-item:nth-of-type(2), #detailBulletsWrapper_feature_div li:nth-of-type(2), #poExpander .a-list-item:nth-of-type(2)',
    'bullet_point_3': '#feature-bullets .a-list-item:nth-of-type(3), #detailBulletsWrapper_feature_div li:nth-of-type(3), #poExpander .a-list-item:nth-of-type(3)',
    'bullet_point_4': '#feature-bullets .a-list-item:nth-of-type(4), #detailBulletsWrapper_feature_div li:nth-of-type(4), #poExpander .a-list-item:nth-of-type(4)',
    'bullet_point_5': '#feature-bullets .a-list-item:nth-of-type(5), #detailBulletsWrapper_feature_div li:nth-of-type(5), #poExpander .a-list-item:nth-of-type(5)',
    'bullet_point_6': '#feature-bullets .a-list-item:nth-of-type(6), #detailBulletsWrapper_feature_div li:nth-of-type(6), #poExpander .a-list-item:nth-of-type(6)',
    
    # Images
    'image_1_source': '#landingImage@src',
    'image_2_source': '#altImages .item:nth-of-type(2) img@src',
    'image_3_source': '#altImages .item:nth-of-type(3) img@src',
    'image_4_source': '#altImages .item:nth-of-type(4) img@src',
    'image_5_source': '#altImages .item:nth-of-type(5) img@src',
    'image_6_source': '#altImages .item:nth-of-type(6) img@src',
    'image_7_source': '#altImages .item:nth-of-type(7) img@src',
    'image_8_source': '#altImages .item:nth-of-type(8) img@src',
    'image_9_source': '#altImages .item:nth-of-type(9) img@src',
    'featured_image_source': '#landingImage@src',
    'other_images_source': '#altImages .item img@src',
    
    # Categories
    'categories': '#wayfinding-breadcrumbs_feature_div .a-link-normal',
    'categories_links': '#wayfinding-breadcrumbs_feature_div .a-link-normal@href',
    
    # Best Seller Information
    'best_seller_category': '#zeitgeistBadge_feature_div .a-link-normal',
    'best_seller_link_1': '#zeitgeistBadge_feature_div .a-link-normal:nth-of-type(1)@href',
    'best_seller_link_2': '#zeitgeistBadge_feature_div .a-link-normal:nth-of-type(2)@href',
    'best_seller_rank_1': '#SalesRank .zg_hrsr_rank:nth-of-type(1)',
    'best_seller_rank_2': '#SalesRank .zg_hrsr_rank:nth-of-type(2)',
    
    # Product Dimensions
    'item_weight': '#productDetails_detailBullets_sections1 .a-list-item:contains("Weight") span:last-child',
    'item_weight_unit_of_measure': '#productDetails_detailBullets_sections1 .a-list-item:contains("Weight") span:last-child',
    'item_dimensions_unit': '#productDetails_detailBullets_sections1 .a-list-item:contains("Dimensions") span:last-child',
    'item_length': '#productDetails_detailBullets_sections1 .a-list-item:contains("Dimensions") span:last-child',
    'item_length_unit_of_measure': '#productDetails_detailBullets_sections1 .a-list-item:contains("Dimensions") span:last-child',
    'item_width': '#productDetails_detailBullets_sections1 .a-list-item:contains("Dimensions") span:last-child',
    'item_width_unit_of_measure': '#productDetails_detailBullets_sections1 .a-list-item:contains("Dimensions") span:last-child',
    'item_height': '#productDetails_detailBullets_sections1 .a-list-item:contains("Dimensions") span:last-child',
    'item_height_unit_of_measure': '#productDetails_detailBullets_sections1 .a-list-item:contains("Dimensions") span:last-child',
    
    # Package Information
    'package_dimensions': '#productDetails_detailBullets_sections1 .a-list-item:contains("Package Dimensions") span:last-child',
    'package_weight_unit': '#productDetails_detailBullets_sections1 .a-list-item:contains("Package Weight") span:last-child',
    'package_length': '#productDetails_detailBullets_sections1 .a-list-item:contains("Package Dimensions") span:last-child',
    'package_width': '#productDetails_detailBullets_sections1 .a-list-item:contains("Package Dimensions") span:last-child',
    'package_height': '#productDetails_detailBullets_sections1 .a-list-item:contains("Package Dimensions") span:last-child',
    
    # Product Features
    'capacity': '#productDetails_detailBullets_sections1 .a-list-item:contains("Capacity") span:last-child',
    'has_video': '.videoCountText',
    'has_climate_pledge': '#climatePledgeFriendlyATF',
    
    # A+ Content
    'a_plus_content': '#aplus',
    
    # Detail Tables
    'details_headers': '#productDetails_techSpec_section_1 .prodDetSectionEntry',
    'details_values': '#productDetails_techSpec_section_1 .prodDetAttrValue',
    'feature_headers': '#productDetails_feature_div th.a-span3',
    'feature_values': '#productDetails_feature_div td.a-span9',
    
    # Buy Box Information
    'buybox_winner': '#merchant-info',
    'buybox_winner_link': '#merchant-info a@href',
    'buybox_quantity_max': '#quantity',
    
    # Pricing and Deals
    'has_deal': '#dealBadge',
    'has_coupon': '#couponBadgeRegularVpc',
    'coupon_value': '#vpcButton .a-text-bold',
    
    # Variations
    'current_variation_header': '#twister',
    'variation_1_asins': '#twister #variation_color_name .twisterTextDiv@data-dp-url',
    'variation_1_name': '#variation_color_name .selection',
    'variation_2_asins': '#twister #variation_size_name .twisterTextDiv@data-dp-url',
    'variation_2_name': '#variation_size_name .selection',
    'variation_3_asins': '#twister #variation_style_name .twisterTextDiv@data-dp-url',
    'variation_3_name': '#variation_style_name .selection',
    'variations_asins': '#twister .twisterTextDiv@data-dp-url',
    
    # Offer Listing
    'offers_count': '#mbc-action-panel-wrapper .a-declarative',
}

# Domain-specific selector maps
AMAZON_DOMAIN_SELECTORS = {
    'amazon.com': AMAZON_SELECTORS,
    'amazon.ca': AMAZON_SELECTORS,
    'amazon.com.mx': AMAZON_SELECTORS,
    'amazon.com.br': AMAZON_SELECTORS,
    'amazon.co.uk': AMAZON_SELECTORS,
    'amazon.fr': AMAZON_SELECTORS,
    'amazon.de': AMAZON_SELECTORS,
    'amazon.nl': AMAZON_SELECTORS,
    'amazon.es': AMAZON_SELECTORS,
    'amazon.it': AMAZON_SELECTORS,
    'amazon.com.tr': AMAZON_SELECTORS,
    'amazon.in': AMAZON_SELECTORS,
    'amazon.sa': AMAZON_SELECTORS,
    'amazon.ae': AMAZON_SELECTORS,
    'amazon.eg': AMAZON_SELECTORS,
    'amazon.co.jp': AMAZON_SELECTORS,
    'amazon.com.au': AMAZON_SELECTORS,
    'amazon.sg': AMAZON_SELECTORS,
}

def get_selectors_for_domain(url, marketplace=None):
    """
    Get the appropriate selector map for the given Amazon URL
    
    Args:
        url (str): The Amazon product URL
        marketplace (str, optional): The marketplace name (e.g. "Amazon.com") to override domain detection
        
    Returns:
        dict: Selector map for the matching domain or None if domain not supported
    """
    # If marketplace is provided, try to use it directly
    if marketplace:
        normalized_marketplace = marketplace.lower().replace(' ', '.').replace('.com', '')
        for domain in AMAZON_DOMAIN_SELECTORS:
            if normalized_marketplace in domain or domain in normalized_marketplace:
                return AMAZON_DOMAIN_SELECTORS[domain]
    
    # Otherwise extract domain from URL
    import re
    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
    if domain_match:
        domain = domain_match.group(1)
        # Check if this exact domain is supported
        if domain in AMAZON_DOMAIN_SELECTORS:
            return AMAZON_DOMAIN_SELECTORS[domain]
        
        # Handle www subdomain case
        if domain.startswith('www.'):
            clean_domain = domain[4:]
            if clean_domain in AMAZON_DOMAIN_SELECTORS:
                return AMAZON_DOMAIN_SELECTORS[clean_domain]
    
    # Fallback to amazon.com selectors as a last resort if domain not matched
    return AMAZON_SELECTORS 