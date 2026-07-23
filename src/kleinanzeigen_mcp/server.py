"""
Kleinanzeigen MCP Server - Main entry point.

This MCP server exposes eBay Kleinanzeigen functionality to Claude and other LLM clients.
It provides tools for searching listings and retrieving detailed information.

Supports two transport modes:
- STDIO: For local clients (Claude Desktop, MCP Toolkit)
- SSE: For remote server deployment with HTTP/SSE
"""
import hmac
import logging
import sys
import os
from typing import Literal
from urllib.parse import parse_qs

# Configure logging to stderr only (CRITICAL for STDIO mode)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]  # stderr only!
)
logger = logging.getLogger(__name__)


class ApiKeyAuthMiddleware:
    """Pure ASGI middleware enforcing MCP_API_KEY on protected paths.

    Accepts the key via (in order):
    - ``Authorization: Bearer <key>`` header
    - ``X-API-Key: <key>`` header
    - ``?api_key=<key>`` query parameter (fallback for SSE clients that
      cannot set custom headers, e.g. browser EventSource)

    Public paths (health/info) stay unauthenticated. If MCP_API_KEY is not
    set, the middleware is never installed (see create_sse_server).
    """

    def __init__(self, app, api_key: str, protected_paths=("/sse", "/messages", "/openapi.json")):
        self.app = app
        self.api_key = api_key
        self.protected_paths = protected_paths

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not any(path == p or path.startswith(p + "/") for p in self.protected_paths):
            await self.app(scope, receive, send)
            return

        # HEAD requests carry no response body by definition, so nothing
        # sensitive is exposed — let them through unauthenticated.
        # Rationale: MCP clients like LibreChat probe servers with an
        # unauthenticated HEAD to detect OAuth requirements; a 401 here makes
        # them misclassify the server as "OAuth required" and never attempt
        # the real (API-key-authenticated) connection.
        if scope.get("method") == "HEAD":
            await self.app(scope, receive, send)
            return

        headers = {
            k.decode("latin-1").lower(): v.decode("latin-1")
            for k, v in scope.get("headers", [])
        }
        provided = None
        auth = headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            provided = auth[7:].strip()
        elif headers.get("x-api-key"):
            provided = headers["x-api-key"].strip()
        else:
            qs = parse_qs(scope.get("query_string", b"").decode("latin-1"))
            provided = qs.get("api_key", [None])[0]

        if provided and hmac.compare_digest(provided, self.api_key):
            await self.app(scope, receive, send)
            return

        body = b'{"error":"unauthorized","detail":"Valid API key required (Authorization: Bearer <key> or X-API-Key header)"}'
        # NOTE: deliberately NO `WWW-Authenticate` header on the 401.
        # MCP clients (LibreChat) probe unauthenticated and interpret a Bearer
        # challenge as "OAuth 2.0 required", then never use their statically
        # configured API-key headers. A bare 401 avoids that misclassification.
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
            ],
        })
        await send({"type": "http.response.body", "body": body})


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

    # NOTE: endpoints are raw ASGI classes, not request-functions. Starlette
    # wraps function endpoints with request_response(), which does
    # `await response(scope, receive, send)` on the return value. Both
    # handlers below take over the ASGI channel themselves and return None,
    # so every request ended with `TypeError: 'NoneType' object is not
    # callable` in the logs. Class endpoints are used directly as ASGI apps.
    class SSEApp:
        """Long-lived SSE stream: one per connected MCP client."""

        async def __call__(self, scope, receive, send):
            async with sse.connect_sse(scope, receive, send) as streams:
                await server.run(
                    streams[0], streams[1], server.create_initialization_options()
                )

    class MessagesApp:
        """Accepts JSON-RPC messages POSTed by the client (sends 202 itself)."""

        async def __call__(self, scope, receive, send):
            await sse.handle_post_message(scope, receive, send)
    
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
                "messages": "/messages",
                "openapi": "/openapi.json"
            }
        })
    
    async def handle_openapi(request):
        """OpenAPI specification endpoint for tool discovery."""
        from starlette.responses import JSONResponse
        return JSONResponse({
            "openapi": "3.1.0",
            "info": {
                "title": "eBay Kleinanzeigen Search MCP Server",
                "description": "Model Context Protocol server for searching eBay Kleinanzeigen listings",
                "version": "1.0.0",
                "contact": {
                    "name": "MCP Server",
                    "url": "https://github.com/Sprayer115/ebay-kleinanzeigen-api-mcp"
                }
            },
            "servers": [
                {
                    "url": "/",
                    "description": "MCP SSE Server"
                }
            ],
            "paths": {
                "/": {
                    "get": {
                        "summary": "Health check",
                        "operationId": "health",
                        "responses": {
                            "200": {
                                "description": "Server status",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "status": {"type": "string"},
                                                "server": {"type": "string"},
                                                "version": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/sse": {
                    "get": {
                        "summary": "Server-Sent Events stream",
                        "operationId": "sse_stream",
                        "responses": {
                            "200": {
                                "description": "SSE stream",
                                "content": {
                                    "text/event-stream": {}
                                }
                            }
                        }
                    }
                },
                "/messages": {
                    "post": {
                        "summary": "Send MCP messages",
                        "operationId": "send_message",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "method": {"type": "string"},
                                            "params": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Message received"
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "SearchListingsRequest": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Suchbegriff für eBay Kleinanzeigen"
                            },
                            "location": {
                                "type": "string",
                                "description": "Optional: Standort für die Suche (z.B. 'Berlin', 'München')"
                            },
                            "category": {
                                "type": "string",
                                "description": "Optional: Kategorie (z.B. 'Elektronik', 'Auto')"
                            },
                            "max_results": {
                                "type": "integer",
                                "default": 20,
                                "description": "Maximale Anzahl der Ergebnisse"
                            }
                        },
                        "required": ["query"]
                    },
                    "GetListingDetailsRequest": {
                        "type": "object",
                        "properties": {
                            "listing_url": {
                                "type": "string",
                                "description": "URL des Inserats auf eBay Kleinanzeigen"
                            }
                        },
                        "required": ["listing_url"]
                    }
                }
            },
            "x-mcp": {
                "protocol_version": "2025-06-18",
                "transport": "sse",
                "tools": [
                    {
                        "name": "search_listings",
                        "description": "Suche nach Inseraten auf eBay Kleinanzeigen",
                        "inputSchema": {
                            "$ref": "#/components/schemas/SearchListingsRequest"
                        }
                    },
                    {
                        "name": "get_listing_details",
                        "description": "Hole detaillierte Informationen zu einem spezifischen Inserat",
                        "inputSchema": {
                            "$ref": "#/components/schemas/GetListingDetailsRequest"
                        }
                    }
                ],
                "prompts": [
                    {
                        "name": "find_deals",
                        "description": "Finde die besten Angebote basierend auf Suchkriterien"
                    },
                    {
                        "name": "compare_listings",
                        "description": "Vergleiche mehrere ähnliche Inserate"
                    },
                    {
                        "name": "monitor_search",
                        "description": "Überwache eine Suche auf neue Angebote"
                    }
                ]
            }
        })
    
    # Create Starlette app
    app = Starlette(
        debug=True,
        routes=[
            Route("/", endpoint=handle_health, methods=["GET"]),
            Route("/openapi.json", endpoint=handle_openapi, methods=["GET"]),
            Route("/sse", endpoint=SSEApp(), methods=["GET"]),
            Route("/messages", endpoint=MessagesApp(), methods=["POST"]),
        ],
    )

    # Enforce API key authentication on functional endpoints if configured.
    # Health endpoint (/) stays public for monitoring/healthchecks.
    api_key = os.environ.get("MCP_API_KEY", "").strip()
    if api_key:
        app = ApiKeyAuthMiddleware(app, api_key)
        logger.info("API key authentication ENABLED for /sse, /messages, /openapi.json")
    else:
        logger.warning(
            "MCP_API_KEY is not set - server is running WITHOUT authentication! "
            "Set MCP_API_KEY to protect /sse and /messages."
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
