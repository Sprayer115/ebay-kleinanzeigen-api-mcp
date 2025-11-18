"""Quick debug script to test the client functions and identify timeout issues."""
import asyncio
import logging
import sys
from src.kleinanzeigen_mcp.client import KleinanzeigenClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


async def test_search_basic():
    """Test basic search without filters."""
    logger.info("=" * 60)
    logger.info("TEST 1: Basic search (query='fahrrad', page_count=1)")
    logger.info("=" * 60)
    
    try:
        async with KleinanzeigenClient() as client:
            start_time = asyncio.get_event_loop().time()
            results = await client.search_listings(query="fahrrad", page_count=1)
            elapsed = asyncio.get_event_loop().time() - start_time
            
            logger.info(f"✓ Search completed in {elapsed:.2f}s")
            logger.info(f"✓ Found {len(results)} results")
            if results:
                logger.info(f"✓ First result: {results[0].title}")
            return True
    except Exception as e:
        logger.error(f"✗ Test failed: {e}", exc_info=True)
        return False


async def test_search_with_location():
    """Test search with location filter."""
    logger.info("=" * 60)
    logger.info("TEST 2: Search with location (query='laptop', location='10178', radius=20)")
    logger.info("=" * 60)
    
    try:
        async with KleinanzeigenClient() as client:
            start_time = asyncio.get_event_loop().time()
            results = await client.search_listings(
                query="laptop",
                location="10178",
                radius=20,
                page_count=1
            )
            elapsed = asyncio.get_event_loop().time() - start_time
            
            logger.info(f"✓ Search completed in {elapsed:.2f}s")
            logger.info(f"✓ Found {len(results)} results")
            if results:
                logger.info(f"✓ First result: {results[0].title}")
            return True
    except Exception as e:
        logger.error(f"✗ Test failed: {e}", exc_info=True)
        return False


async def test_search_with_price():
    """Test search with price filter."""
    logger.info("=" * 60)
    logger.info("TEST 3: Search with price (query='gaming pc', min_price=500, max_price=1000)")
    logger.info("=" * 60)
    
    try:
        async with KleinanzeigenClient() as client:
            start_time = asyncio.get_event_loop().time()
            results = await client.search_listings(
                query="gaming pc",
                min_price=500,
                max_price=1000,
                page_count=1
            )
            elapsed = asyncio.get_event_loop().time() - start_time
            
            logger.info(f"✓ Search completed in {elapsed:.2f}s")
            logger.info(f"✓ Found {len(results)} results")
            if results:
                logger.info(f"✓ First result: {results[0].title} - {results[0].price}€")
            return True
    except Exception as e:
        logger.error(f"✗ Test failed: {e}", exc_info=True)
        return False


async def test_listing_details():
    """Test fetching listing details."""
    logger.info("=" * 60)
    logger.info("TEST 4: Get listing details")
    logger.info("=" * 60)
    
    try:
        # First, get a real listing ID from search
        async with KleinanzeigenClient() as client:
            logger.info("  → First searching for a listing...")
            results = await client.search_listings(query="fahrrad", page_count=1)
            
            if not results:
                logger.warning("✗ No results to test with")
                return False
            
            listing_id = results[0].adid
            logger.info(f"  → Testing with ID: {listing_id}")
            
            start_time = asyncio.get_event_loop().time()
            details = await client.get_listing_details(listing_id)
            elapsed = asyncio.get_event_loop().time() - start_time
            
            logger.info(f"✓ Details fetched in {elapsed:.2f}s")
            logger.info(f"✓ Title: {details.title}")
            logger.info(f"✓ Status: {details.status}")
            logger.info(f"✓ Images: {len(details.images)} found")
            return True
    except Exception as e:
        logger.error(f"✗ Test failed: {e}", exc_info=True)
        return False


async def test_timeout_scenario():
    """Test with very short timeout to see behavior."""
    logger.info("=" * 60)
    logger.info("TEST 5: Short timeout scenario")
    logger.info("=" * 60)
    
    try:
        async with KleinanzeigenClient() as client:
            # Attempt a search with timeout monitoring
            try:
                results = await asyncio.wait_for(
                    client.search_listings(query="test", page_count=1),
                    timeout=5.0  # 5 second timeout
                )
                logger.info(f"✓ Completed within 5s timeout, {len(results)} results")
                return True
            except asyncio.TimeoutError:
                logger.error("✗ Operation exceeded 5s timeout")
                return False
    except Exception as e:
        logger.error(f"✗ Test failed: {e}", exc_info=True)
        return False


async def main():
    """Run all tests."""
    logger.info("\n")
    logger.info("=" * 60)
    logger.info("KLEINANZEIGEN CLIENT DEBUG TESTS")
    logger.info("=" * 60)
    logger.info("\n")
    
    tests = [
        ("Basic Search", test_search_basic),
        ("Search with Location", test_search_with_location),
        ("Search with Price Filter", test_search_with_price),
        ("Listing Details", test_listing_details),
        ("Timeout Scenario", test_timeout_scenario),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
            logger.info("\n")
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
            logger.info("\n")
    
    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    for test_name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        logger.info(f"{status}: {test_name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
