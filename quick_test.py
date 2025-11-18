"""Quick test to identify timeout issues."""
import asyncio
import logging
import sys
import time
from src.kleinanzeigen_mcp.client import KleinanzeigenClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def quick_test():
    """Quick test with timing."""
    logger.info("Starting quick test...")
    
    try:
        start = time.time()
        logger.info("1. Creating client...")
        
        async with KleinanzeigenClient() as client:
            init_time = time.time() - start
            logger.info(f"   ✓ Client initialized in {init_time:.2f}s")
            
            # Test simple search
            search_start = time.time()
            logger.info("2. Running search (query='laptop', page_count=1)...")
            
            results = await asyncio.wait_for(
                client.search_listings(query="laptop", page_count=1),
                timeout=60.0
            )
            
            search_time = time.time() - search_start
            logger.info(f"   ✓ Search completed in {search_time:.2f}s")
            logger.info(f"   ✓ Found {len(results)} results")
            
            if results:
                logger.info(f"   ✓ First result: {results[0].title[:50]}...")
                logger.info(f"   ✓ Price: {results[0].price}€")
                logger.info(f"   ✓ ID: {results[0].adid}")
                
                # Test details
                detail_start = time.time()
                logger.info("3. Fetching details for first result...")
                
                details = await asyncio.wait_for(
                    client.get_listing_details(results[0].adid),
                    timeout=60.0
                )
                
                detail_time = time.time() - detail_start
                logger.info(f"   ✓ Details fetched in {detail_time:.2f}s")
                logger.info(f"   ✓ Status: {details.status}")
                logger.info(f"   ✓ Images: {len(details.images)}")
            
            total_time = time.time() - start
            logger.info(f"\nTotal test time: {total_time:.2f}s")
            logger.info("✓ All tests passed!")
            
    except asyncio.TimeoutError:
        logger.error("✗ Operation timed out!")
    except Exception as e:
        logger.error(f"✗ Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(quick_test())
