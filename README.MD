# Kleinanzeigen MCP Server

<div align="center">
  <h3 align="center">MCP Server for eBay Kleinanzeigen</h3>

  <p align="center">
    Connect Claude AI to eBay Kleinanzeigen - Search listings and get details through natural language.
  </p>

  <p align="center">
    <b>🤖 Model Context Protocol Server</b>
    <br />
    ✓ Natural Language Search (German + English)
    <br />
    ✓ Detailed Listing Information
    <br />
    ✓ Built for Claude Desktop
    <br />
    ✓ Docker & Local Installation
  </p>
</div>

---

> **Note:** This is a complete rewrite of the original [DanielWTE/ebay-kleinanzeigen-api](https://github.com/DanielWTE/ebay-kleinanzeigen-api) project.  
> Original project was a FastAPI REST API. This version is a **Model Context Protocol (MCP) server** specifically designed for Claude Desktop integration.
> 
> **Key Changes:**
> - ✅ MCP Protocol instead of REST API
> - ✅ Direct Claude Desktop integration
> - ✅ UV package manager (10-100x faster)
> - ✅ Comprehensive test suite
> - ✅ Docker support with MCP Toolkit
> - ✅ German language optimization

---

## 🚀 Quick Start

**Choose your preferred installation method:**

### 🐳 Docker (Recommended for Production)
```powershell
# With Docker MCP Toolkit (easiest)
# See: DOCKER_QUICKSTART.md

docker build -t kleinanzeigen-mcp:latest -f Dockerfile.mcp .
# Then follow DOCKER_QUICKSTART.md for catalog setup
```

### 💻 Local Installation (Recommended for Development)

#### 1. Install
```powershell
.\setup-uv.ps1
```

#### 2. Configure Claude Desktop
Copy the generated config to: `%APPDATA%\Claude\claude_desktop_config.json`

### 3. Test
Restart Claude Desktop and try: **"Search for laptops in Berlin under 500€"**

See [START_HERE.md](START_HERE.md) for detailed instructions.

## 📦 What is this?

An **MCP (Model Context Protocol) Server** that gives Claude AI direct access to eBay Kleinanzeigen:
- 🔍 Search listings with filters (location, price, keywords)
- 📄 Get complete listing details (images, seller info, specs)
- 🤖 Works through natural language in Claude Desktop

## 🛠️ Available Tools

### `search_listings`
Search with optional filters:
- `query` - Keywords (e.g., "laptop", "fahrrad")
- `location` - City or postal code
- `radius` - Distance in km
- `min_price` / `max_price` - Price range in EUR
- `page_count` - Number of pages (1-20)

### `get_listing_details`
### `get_listing_details`
Get complete info for a specific listing by ID.

## 💡 Example Usage

**User:** "Find bicycles in Munich under 300€"

**Claude:** 
1. Calls `search_listings(query="fahrrad", location="München", max_price=300)`
2. Shows results with IDs, prices, links
3. Can get details: `get_listing_details(listing_id="...")`
4. Provides recommendations

## 🔧 Development

```powershell
# Run server
uv run kleinanzeigen-mcp

# Run tests (unit tests only, fast)
uv run pytest

# Run ALL tests (includes slow integration tests)
uv run pytest --run-integration

# Run with verbose output
uv run pytest -v

# Debug mode
$env:LOG_LEVEL="DEBUG"
uv run kleinanzeigen-mcp
```

## 🐳 Docker

```powershell
docker compose --profile stdio up -d
```

## 📚 Documentation

- **[START_HERE.md](START_HERE.md)** - Quick setup guide
- **MCP Protocol:** https://modelcontextprotocol.io
- **Issues:** https://github.com/DanielWTE/ebay-kleinanzeigen-api/issues

## 🔐 Privacy

- No personal data in repository
- Config files auto-generated with your paths
- `.gitignore` protects sensitive files

---

**Status:** ✅ Ready to use with Claude Desktop

## License
Distributed under the MIT License. See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>
