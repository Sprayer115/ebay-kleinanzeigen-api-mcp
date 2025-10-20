"""
Kleinanzeigen MCP Server - Main entry point.

This MCP server exposes eBay Kleinanzeigen functionality to Claude and other LLM clients.
It provides tools for searching listings and retrieving detailed information.

Supports two transport modes:
- STDIO: For local clients (Claude Desktop, MCP Toolkit)
- SSE: For remote server deployment with HTTP/SSE
"""
import logging
import sys
import os
from typing import Literal

# Configure logging to stderr only (CRITICAL for STDIO mode)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]  # stderr only!
)
logger = logging.getLogger(__name__)


def get_transport_mode() -> Literal["stdio", "sse"]:
    """Get transport mode from environment variable."""
    mode = os.environ.get("TRANSPORT_MODE", "stdio").lower()
    if mode not in ["stdio", "sse"]:
        logger.warning(f"Invalid TRANSPORT_MODE '{mode}', defaulting to 'stdio'")
        return "stdio"
    return mode  # type: ignore


def create_stdio_server():
    """Create MCP server for STDIO transport (local clients)."""
    from mcp.server.fastmcp import FastMCP
    
    mcp = FastMCP(name="ebay-kleinanzeigen-search")
    
    # Register all tools and prompts
    from .tools import register_listing_tools
    from .prompts import register_prompts
    
    register_listing_tools(mcp)
    register_prompts(mcp)
    
    logger.info("Kleinanzeigen MCP Server initialized (STDIO mode)")
    logger.info("Available tools: search_listings, get_listing_details")
    logger.info("Available prompts: find_deals, compare_listings, monitor_search")
    
    return mcp


def create_sse_server():
    """Create MCP server for SSE transport (remote server deployment)."""
    from mcp.server import Server
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route
    import uvicorn
    
    # Create MCP server instance
    server = Server(name="ebay-kleinanzeigen-search")
    
    # Register tools manually (FastMCP's decorators won't work here)
    from .tools import register_listing_tools_manual
    from .prompts import register_prompts_manual
    
    register_listing_tools_manual(server)
    register_prompts_manual(server)
    
    logger.info("Kleinanzeigen MCP Server initialized (SSE mode)")
    logger.info("Available tools: search_listings, get_listing_details")
    logger.info("Available prompts: find_deals, compare_listings, monitor_search")
    
    # Create SSE transport
    sse = SseServerTransport("/messages")
    
    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )
    
    async def handle_messages(request):
        await sse.handle_post_message(request.scope, request.receive, request._send)
    
    async def handle_health(request):
        """Health check endpoint for monitoring and OpenWebUI."""
        from starlette.responses import JSONResponse
        return JSONResponse({
            "status": "ok",
            "server": "ebay-kleinanzeigen-search",
            "version": "1.0.0",
            "transport": "sse",
            "endpoints": {
                "health": "/",
                "sse": "/sse",
                "messages": "/messages"
            }
        })
    
    # Create Starlette app
    app = Starlette(
        debug=True,
        routes=[
            Route("/", endpoint=handle_health, methods=["GET"]),
            Route("/sse", endpoint=handle_sse),
            Route("/messages", endpoint=handle_messages, methods=["POST"]),
        ],
    )
    
    # Get configuration from environment
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    
    logger.info(f"Starting SSE server on {host}:{port}")
    
    return app, host, port


def main():
    """Main entry point for the MCP server."""
    transport_mode = get_transport_mode()
    logger.info(f"Starting Kleinanzeigen MCP Server (transport: {transport_mode})...")
    
    if transport_mode == "stdio":
        # STDIO mode: Standard MCP server for local clients
        mcp = create_stdio_server()
        mcp.run()
    else:
        # SSE mode: HTTP/SSE server for remote deployment
        import uvicorn
        app, host, port = create_sse_server()
        uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
