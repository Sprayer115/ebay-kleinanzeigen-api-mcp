"""
Simple smoke tests for Kleinanzeigen MCP Server.
These tests don't hit the real website.
"""
import pytest
from kleinanzeigen_mcp.types import ListingSummary, ListingDetails


def test_imports():
    """Test that all modules can be imported."""
    from kleinanzeigen_mcp.client import KleinanzeigenClient
    from kleinanzeigen_mcp.server import main
    from kleinanzeigen_mcp.tools.listings import register_listing_tools
    from kleinanzeigen_mcp.prompts.workflows import register_prompts
    assert True


def test_listing_summary_structure():
    """Test ListingSummary dataclass structure."""
    listing = ListingSummary(
        adid="123",
        url="https://example.com",
        title="Test Item",
        price="100€",
        description="Test description"
    )
    assert listing.adid == "123"
    assert listing.title == "Test Item"
    assert listing.price == "100€"


def test_listing_details_structure():
    """Test ListingDetails dataclass structure."""
    details = ListingDetails(
        id="123",
        categories=["Electronics"],
        title="Test Item",
        status="active",
        price="100€",
        delivery="shipping",
        location={"city": "Berlin"},
        views="100",
        description="Test description",
        images=["https://example.com/1.jpg"],
        details={"Zustand": "Neu"},
        features={"feature1": "value1"},
        seller={"name": "Test Seller"},
        extra_info={}
    )
    assert details.id == "123"
    assert details.title == "Test Item"
    assert isinstance(details.images, list)
    assert isinstance(details.details, dict)
