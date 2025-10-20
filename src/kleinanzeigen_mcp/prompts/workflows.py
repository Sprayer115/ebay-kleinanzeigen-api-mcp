"""Prompt templates for Kleinanzeigen MCP Server."""
import logging
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_prompts(mcp: FastMCP):
    """Register prompt templates for common workflows."""
    
    @mcp.prompt()
    def find_deals(
        item_type: str,
        max_budget: int,
        location: str = "Germany"
    ) -> str:
        """
        Help users find the best deals for a specific item type within budget.
        
        Args:
            item_type: What to search for (e.g., "laptop", "bicycle", "furniture")
            max_budget: Maximum price in EUR
            location: Location or postal code for local search
        
        Returns:
            Prompt template for finding deals
        """
        return f"""You are helping a user find the best deals for {item_type} on eBay Kleinanzeigen.

**User Requirements:**
- Item: {item_type}
- Maximum Budget: {max_budget}€
- Location: {location}

**Your Task:**
1. Use search_listings to find available {item_type} items under {max_budget}€ in {location}
2. Sort results mentally by value (price vs. features/condition)
3. For the top 3-5 most promising listings, use get_listing_details to get full information
4. Compare and present:
   - Price comparison
   - Condition analysis
   - Location/delivery convenience
   - Seller reputation indicators
5. Provide a recommendation with reasoning

**Output Format:**
- Summary table of best options
- Detailed analysis of top recommendation
- Pros/cons for each option
- Action steps for the user

Begin your search now."""
    
    @mcp.prompt()
    def compare_listings(
        listing_ids: str
    ) -> str:
        """
        Compare multiple listings side-by-side to help decision-making.
        
        Args:
            listing_ids: Comma-separated listing IDs to compare (e.g., "123,456,789")
        
        Returns:
            Prompt template for comparison
        """
        ids = [id.strip() for id in listing_ids.split(",")]
        return f"""You are helping a user compare multiple eBay Kleinanzeigen listings.

**Listings to Compare:**
{', '.join(ids)}

**Your Task:**
1. Use get_listing_details for each listing ID
2. Create a comparison table with:
   - Price
   - Condition/Status
   - Location & Delivery
   - Key Features
   - Seller Information
3. Highlight:
   - Best value for money
   - Most convenient option
   - Any concerns or red flags
4. Provide a clear recommendation

**Output Format:**
- Side-by-side comparison table
- Key differences highlighted
- Recommendation with reasoning
- Questions user should ask sellers

Begin the comparison now."""
    
    @mcp.prompt()
    def monitor_search(
        query: str,
        location: str = "",
        max_price: int = 0
    ) -> str:
        """
        Set up a search monitoring strategy for new listings.
        
        Args:
            query: Search keywords
            location: Optional location filter
            max_price: Optional maximum price
        
        Returns:
            Prompt template for monitoring setup
        """
        filters = f"query: {query}"
        if location:
            filters += f", location: {location}"
        if max_price > 0:
            filters += f", max price: {max_price}€"
            
        return f"""You are helping a user monitor new listings on eBay Kleinanzeigen.

**Search Parameters:**
{filters}

**Your Task:**
1. Perform initial search using search_listings
2. Document current results (count, price range, typical offerings)
3. Provide the user with:
   - Current market overview
   - Typical price range for these items
   - Search optimization tips
   - Recommended check frequency
4. Create a monitoring checklist:
   - What to look for in new listings
   - Red flags to avoid
   - Quick decision criteria

**Output Format:**
- Current market snapshot
- Search optimization suggestions
- Monitoring strategy
- Quick evaluation checklist

Begin the analysis now."""
    
    logger.info("Registered prompt templates: find_deals, compare_listings, monitor_search")
