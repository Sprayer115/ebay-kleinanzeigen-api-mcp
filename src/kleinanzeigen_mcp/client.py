"""Kleinanzeigen scraping client - centralized interface to the website."""
import logging
from typing import Optional, List, Dict, Any
from urllib.parse import urlencode
from playwright.async_api import Page, Browser, async_playwright
import re

from .types import ListingSummary, ListingDetails, SearchError, DetailFetchError

logger = logging.getLogger(__name__)


class KleinanzeigenClient:
    """
    Centralized client for interacting with Kleinanzeigen.de.
    Manages browser lifecycle and provides clean API for operations.
    """
    
    def __init__(self):
        self.base_url = "https://www.kleinanzeigen.de"
        self.playwright = None
        self.browser: Optional[Browser] = None
        
    async def __aenter__(self):
        """Async context manager entry - initializes browser."""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleans up browser."""
        await self.close()
        
    async def start(self):
        """Initialize Playwright and browser."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            logger.info("Browser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise SearchError(f"Browser initialization failed: {e}")
    
    async def close(self):
        """Clean up browser and Playwright resources."""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    async def search_listings(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        radius: Optional[int] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        page_count: int = 1
    ) -> List[ListingSummary]:
        """
        Search for listings with optional filters.
        
        Args:
            query: Search keywords (e.g., "fahrrad")
            location: Location or postal code (e.g., "10178")
            radius: Search radius in km
            min_price: Minimum price in EUR
            max_price: Maximum price in EUR
            page_count: Number of result pages to fetch (1-20)
            
        Returns:
            List of ListingSummary objects
            
        Raises:
            SearchError: If search operation fails
        """
        if not self.browser:
            raise SearchError("Browser not initialized. Call start() first.")
        
        # Validate page_count
        if page_count < 1 or page_count > 20:
            page_count = max(1, min(20, page_count))
            logger.warning(f"page_count clamped to valid range: {page_count}")
        
        # Build URL with price filter
        price_path = ""
        if min_price is not None or max_price is not None:
            min_price_str = str(min_price) if min_price is not None else ""
            max_price_str = str(max_price) if max_price is not None else ""
            price_path = f"/preis:{min_price_str}:{max_price_str}"
        
        search_path = f"{price_path}/s-seite:{{page}}"
        
        # Build query parameters
        params = {}
        if query:
            params['keywords'] = query
        if location:
            params['locationStr'] = location
        if radius:
            params['radius'] = radius
        
        search_url = self.base_url + search_path + ("?" + urlencode(params) if params else "")
        
        results = []
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            for page_num in range(1, page_count + 1):
                current_url = search_url.format(page=page_num)
                logger.info(f"Fetching page {page_num}: {current_url}")
                
                await page.goto(current_url, timeout=30000, wait_until="domcontentloaded")
                # Wait for either the listing container or "no results" message
                try:
                    await page.wait_for_selector(".ad-listitem, .l-splitpage--no-results", timeout=10000)
                except Exception as e:
                    logger.warning(f"Selector wait failed: {e}, continuing anyway")
                
                page_results = await self._extract_listings_from_page(page)
                results.extend(page_results)
                
                if not page_results and page_num == 1:
                    logger.warning("No results found on first page")
                    break
                    
            logger.info(f"Search completed: {len(results)} listings found")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise SearchError(f"Failed to search listings: {e}")
        finally:
            await page.close()
            await context.close()
    
    async def _extract_listings_from_page(self, page: Page) -> List[ListingSummary]:
        """Extract listing data from a search results page."""
        try:
            items = await page.query_selector_all(".ad-listitem:not(.is-topad):not(.badge-hint-pro-small-srp)")
            results = []
            
            for item in items:
                article = await item.query_selector("article")
                if not article:
                    continue
                
                data_adid = await article.get_attribute("data-adid")
                data_href = await article.get_attribute("data-href")
                
                # Extract title
                title_element = await article.query_selector("h2.text-module-begin a.ellipsis")
                title_text = await title_element.inner_text() if title_element else ""
                
                # Extract price
                price_element = await article.query_selector("p.aditem-main--middle--price-shipping--price")
                price_text = ""
                if price_element:
                    price_text = await price_element.inner_text()
                    price_text = price_text.replace("€", "").replace("VB", "").replace(".", "").strip()
                
                # Extract description
                desc_element = await article.query_selector("p.aditem-main--middle--description")
                description_text = await desc_element.inner_text() if desc_element else ""
                
                if data_adid and data_href:
                    full_url = f"{self.base_url}{data_href}"
                    results.append(ListingSummary(
                        adid=data_adid,
                        url=full_url,
                        title=title_text,
                        price=price_text,
                        description=description_text
                    ))
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to extract listings from page: {e}")
            return []
    
    async def get_listing_details(self, listing_id: str) -> ListingDetails:
        """
        Fetch complete details for a specific listing.
        
        Args:
            listing_id: The unique ad ID (e.g., "2937345678")
            
        Returns:
            ListingDetails object with complete information
            
        Raises:
            DetailFetchError: If detail fetch fails
        """
        if not self.browser:
            raise DetailFetchError("Browser not initialized. Call start() first.")
        
        url = f"{self.base_url}/s-anzeige/{listing_id}"
        context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            logger.info(f"Fetching details for listing {listing_id}")
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            # Wait for view counter (optional, may not appear)
            try:
                await page.wait_for_selector("#viewad-cntr-num", state="visible", timeout=2500)
            except:
                logger.debug("View counter did not appear")
            
            # Extract all details
            details = await self._extract_listing_details(page)
            logger.info(f"Successfully fetched details for {listing_id}")
            return details
            
        except Exception as e:
            logger.error(f"Failed to fetch listing details: {e}")
            raise DetailFetchError(f"Failed to fetch listing {listing_id}: {e}")
        finally:
            await page.close()
            await context.close()
    
    async def _extract_listing_details(self, page: Page) -> ListingDetails:
        """Extract complete listing information from detail page."""
        # Helper functions for extraction
        async def get_text(selector: str, default: str = "") -> str:
            element = await page.query_selector(selector)
            if element:
                text = await element.inner_text()
                return text.strip()
            return default
        
        async def get_texts(selector: str) -> List[str]:
            elements = await page.query_selector_all(selector)
            texts = []
            for elem in elements:
                text = await elem.inner_text()
                if text.strip():
                    texts.append(text.strip())
            return texts
        
        # Extract basic info
        ad_id = await get_text("#viewad-ad-id-box > ul > li:nth-child(2)", "[ERROR] ID not found")
        categories = await get_texts(".breadcrump-link")
        title = await get_text("#viewad-title", "[ERROR] Title not found")
        
        # Determine status
        status = "active"
        title_element = await page.query_selector("#viewad-title")
        if title_element:
            title_text = await title_element.inner_text()
            if "Verkauft" in title_text:
                status = "sold"
            elif "Reserviert •" in title_text:
                status = "reserved"
            elif "Gelöscht •" in title_text:
                status = "deleted"
        
        if await page.query_selector(".badge-sold"):
            status = "sold"
        
        # Clean title
        if " • " in title:
            title = title.split(" • ")[-1].strip()
        
        # Extract price
        price_text = await get_text("#viewad-price")
        price = self._parse_price(price_text)
        
        # Extract views
        views = await get_text("#viewad-cntr-num", "0")
        
        # Extract description
        description = await get_text("#viewad-description-text")
        if description:
            description = re.sub(r'[ \t]+', ' ', description).strip()
            description = re.sub(r'\n+', '\n', description)
        
        # Extract images
        images = []
        image_elements = await page.query_selector_all("#viewad-image img")
        for img in image_elements:
            src = await img.get_attribute("src")
            if src:
                images.append(src)
        
        # Extract shipping info
        shipping = None
        shipping_text = await get_text(".boxedarticle--details--shipping")
        if shipping_text:
            if "Nur Abholung" in shipping_text:
                shipping = "pickup"
            elif "Versand" in shipping_text:
                shipping = "shipping"
        
        # Extract location
        location_text = await get_text("#viewad-locality")
        location = {"raw": location_text} if location_text else {}
        
        # Extract seller details
        seller = {}
        seller_name = await get_text(".userprofile--name")
        if seller_name:
            seller["name"] = seller_name
        
        # Extract details section
        details = {}
        if await page.query_selector("#viewad-details"):
            detail_items = await page.query_selector_all("#viewad-details .addetailslist--detail")
            for item in detail_items:
                label_elem = await item.query_selector(".addetailslist--detail--label")
                value_elem = await item.query_selector(".addetailslist--detail--value")
                if label_elem and value_elem:
                    label = (await label_elem.inner_text()).strip()
                    value = (await value_elem.inner_text()).strip()
                    details[label] = value
        
        # Extract features
        features = {}
        if await page.query_selector("#viewad-configuration"):
            feature_items = await page.query_selector_all("#viewad-configuration .addetailslist--detail")
            for item in feature_items:
                label_elem = await item.query_selector(".addetailslist--detail--label")
                value_elem = await item.query_selector(".addetailslist--detail--value")
                if label_elem and value_elem:
                    label = (await label_elem.inner_text()).strip()
                    value = (await value_elem.inner_text()).strip()
                    features[label] = value
        
        return ListingDetails(
            id=ad_id,
            categories=categories,
            title=title,
            status=status,
            price=price,
            delivery=shipping,
            location=location,
            views=views,
            description=description,
            images=images,
            details=details,
            features=features,
            seller=seller,
            extra_info={}
        )
    
    def _parse_price(self, price_text: str) -> Optional[str]:
        """Parse price from text, handling various formats."""
        if not price_text:
            return None
        
        # Remove common non-numeric characters
        cleaned = price_text.replace("€", "").replace("VB", "").replace(".", "").strip()
        
        # Return cleaned price or None if it's empty
        return cleaned if cleaned else None
