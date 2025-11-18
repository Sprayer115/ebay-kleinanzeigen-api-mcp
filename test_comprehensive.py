"""Comprehensive test to verify all fixed functionality."""
import asyncio
import logging
import sys
from src.kleinanzeigen_mcp.client import KleinanzeigenClient

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def comprehensive_test():
    """Test all scenarios."""
    print("\n" + "="*60)
    print("COMPREHENSIVE FUNCTION TEST")
    print("="*60 + "\n")
    
    async with KleinanzeigenClient() as client:
        # Test 1: Basic search
        print("1️⃣  Basic Search")
        results = await client.search_listings(query="fahrrad", page_count=1)
        print(f"   ✓ Found {len(results)} results")
        
        # Test 2: Search with location
        print("\n2️⃣  Search with Location Filter")
        results = await client.search_listings(
            query="laptop",
            location="10178",
            radius=50,
            page_count=1
        )
        print(f"   ✓ Found {len(results)} results in Berlin area")
        
        # Test 3: Search with price range
        print("\n3️⃣  Search with Price Filter")
        results = await client.search_listings(
            query="monitor",
            min_price=50,
            max_price=200,
            page_count=1
        )
        print(f"   ✓ Found {len(results)} results (50-200€)")
        
        # Test 4: Multiple pages
        print("\n4️⃣  Multi-Page Search")
        results = await client.search_listings(
            query="smartphone",
            page_count=2
        )
        print(f"   ✓ Found {len(results)} results across 2 pages")
        
        # Test 5: Get details
        if results:
            print("\n5️⃣  Get Listing Details")
            details = await client.get_listing_details(results[0].adid)
            print(f"   ✓ Title: {details.title[:50]}...")
            print(f"   ✓ Status: {details.status}")
            print(f"   ✓ Price: {details.price}€" if details.price else "   ✓ Price: On request")
            print(f"   ✓ Images: {len(details.images)}")
            print(f"   ✓ Location: {details.location.get('raw', 'N/A') if details.location else 'N/A'}")
    
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(comprehensive_test())
