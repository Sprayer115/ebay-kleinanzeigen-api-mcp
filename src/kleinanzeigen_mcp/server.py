"""
Kleinanzeigen MCP Server - Main entry point.

This MCP server exposes eBay Kleinanzeigen functionality to Claude and other LLM clients.
It provides tools for searching listings and retrieving detailed information.
"""
import logging
import sys
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr only (CRITICAL for STDIO mode)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]  # stderr only!
)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP(
    name="ebay-kleinanzeigen-search"
)

# Register all tools and prompts
from .tools import register_listing_tools
from .prompts import register_prompts

register_listing_tools(mcp)
register_prompts(mcp)

logger.info("Kleinanzeigen MCP Server initialized successfully")
logger.info("Available tools: search_listings, get_listing_details")
logger.info("Available prompts: find_deals, compare_listings, monitor_search")


def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Kleinanzeigen MCP Server...")
    mcp.run()


if __name__ == "__main__":
    main()
