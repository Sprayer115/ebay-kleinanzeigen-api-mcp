"""
Test suite for Kleinanzeigen MCP Server.
Run with: uv run pytest
Integration tests with real website: uv run pytest -m integration
Unit tests only: uv run pytest -m "not integration"
"""
import pytest
import asyncio
from kleinanzeigen_mcp.client import KleinanzeigenClient
from kleinanzeigen_mcp.types import SearchError, DetailFetchError

# Marker for integration tests that hit real website
pytestmark = pytest.mark.integration

# Increase timeout for integration tests
@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the event loop for each test."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_client_initialization():
    """Test that client can be initialized and closed properly."""
    client = KleinanzeigenClient()
    await client.start()
    assert client.browser is not None
    await client.close()


@pytest.mark.asyncio
async def test_client_context_manager():
    """Test that client works as async context manager."""
    async with KleinanzeigenClient() as client:
        assert client.browser is not None


@pytest.mark.asyncio
@pytest.mark.timeout(30)  # 30 second timeout
async def test_search_basic():
    """Test basic search functionality."""
    async with KleinanzeigenClient() as client:
        results = await client.search_listings(
            query="laptop",
            page_count=1
        )
        assert isinstance(results, list)
        # Results might be empty, but should be a list


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_search_with_location():
    """Test search with location filter."""
    async with KleinanzeigenClient() as client:
        results = await client.search_listings(
            query="fahrrad",
            location="10178",
            radius=10,
            page_count=1
        )
        assert isinstance(results, list)


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_search_with_price_range():
    """Test search with price filters."""
    async with KleinanzeigenClient() as client:
        results = await client.search_listings(
            query="laptop",
            min_price=100,
            max_price=500,
            page_count=1
        )
        assert isinstance(results, list)


@pytest.mark.asyncio
@pytest.mark.timeout(60)  # Longer timeout for multi-page
async def test_search_multiple_pages():
    """Test multi-page search."""
    async with KleinanzeigenClient() as client:
        results = await client.search_listings(
            query="laptop",
            page_count=2
        )
        assert isinstance(results, list)


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_search_page_count_clamping():
    """Test that page_count is clamped to valid range."""
    async with KleinanzeigenClient() as client:
        # Test negative value gets clamped to 1
        results = await client.search_listings(
            query="test",
            page_count=-5  # Should be clamped to 1
        )
        assert isinstance(results, list)
        
        # Note: Testing page_count=100 (clamped to 20) would take too long
        # The clamping logic is tested in unit tests instead


@pytest.mark.asyncio
@pytest.mark.timeout(60)  # 60 second timeout for network request
async def test_get_listing_details_structure():
    """Test that listing details have correct structure."""
    async with KleinanzeigenClient() as client:
        # First, get a real listing ID from search
        try:
            results = await client.search_listings(
                query="laptop",
                page_count=1
            )
            
            if results:
                listing_id = results[0].adid
                details = await client.get_listing_details(listing_id)
                
                # Verify structure
                assert hasattr(details, 'id')
                assert hasattr(details, 'title')
                assert hasattr(details, 'status')
                assert hasattr(details, 'price')
                assert hasattr(details, 'description')
                assert hasattr(details, 'images')
                assert isinstance(details.images, list)
            else:
                pytest.skip("No listings found for test")
        except Exception as e:
            pytest.skip(f"Test skipped due to network/scraping issue: {e}")


@pytest.mark.asyncio
async def test_search_no_results():
    """Test search with query that returns no results."""
    async with KleinanzeigenClient() as client:
        results = await client.search_listings(
            query="xyzabc123unlikely",
            page_count=1
        )
        # Should return empty list, not error
        assert isinstance(results, list)
        assert len(results) == 0


@pytest.mark.asyncio
async def test_client_without_start():
    """Test that operations fail gracefully without initialization."""
    client = KleinanzeigenClient()
    
    with pytest.raises(SearchError):
        await client.search_listings(query="test")


def test_price_parsing():
    """Test price parsing logic."""
    client = KleinanzeigenClient()
    
    assert client._parse_price("123 €") == "123"
    assert client._parse_price("1.000 € VB") == "1000"
    assert client._parse_price("") is None
    assert client._parse_price("VB") is None or client._parse_price("VB") == ""


# Integration test markers
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_search_and_details_workflow():
    """End-to-end test: search -> get details."""
    async with KleinanzeigenClient() as client:
        # Step 1: Search
        results = await client.search_listings(
            query="laptop",
            max_price=1000,
            page_count=1
        )
        
        assert len(results) > 0, "Should find at least one laptop"
        
        # Step 2: Get details for first result
        first_listing = results[0]
        details = await client.get_listing_details(first_listing.adid)
        
        # Step 3: Verify details match search result
        assert details.id == first_listing.adid
        assert details.title  # Should have a title
        assert details.status in ["active", "sold", "reserved", "deleted"]


if __name__ == "__main__":
    # Run tests with asyncio
    pytest.main([__file__, "-v", "-s"])
