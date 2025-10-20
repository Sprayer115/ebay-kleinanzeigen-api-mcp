"""Types and data models for Kleinanzeigen MCP Server."""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class ListingSearchParams:
    """Parameters for searching listings."""
    query: Optional[str] = None
    location: Optional[str] = None
    radius: Optional[int] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    page_count: int = 1


@dataclass
class ListingSummary:
    """Summary information from search results."""
    adid: str
    url: str
    title: str
    price: str
    description: str


@dataclass
class ListingDetails:
    """Complete listing information."""
    id: str
    categories: List[str]
    title: str
    status: str
    price: Optional[str]
    delivery: Optional[str]
    location: Optional[Dict[str, Any]]
    views: str
    description: str
    images: List[str]
    details: Dict[str, Any]
    features: Dict[str, Any]
    seller: Dict[str, Any]
    extra_info: Dict[str, Any]


class KleinanzeigenError(Exception):
    """Base exception for Kleinanzeigen operations."""
    pass


class SearchError(KleinanzeigenError):
    """Error during search operation."""
    pass


class DetailFetchError(KleinanzeigenError):
    """Error fetching listing details."""
    pass
