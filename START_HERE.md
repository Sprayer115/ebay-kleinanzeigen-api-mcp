# Kleinanzeigen MCP Server - Quick Start

## 🚀 Installation (2 Steps)

### 1. Run Setup
```powershell
.\setup-uv.ps1
```

This will:
- Install UV (if needed)
- Create virtual environment
- Install all dependencies
- Install Playwright browser
- Generate Claude config

### 2. Configure Claude Desktop

The setup creates: `claude_desktop_config.example.generated.json`

**Copy its content to:** `%APPDATA%\Claude\claude_desktop_config.json`

Example:
```json
{
  "mcpServers": {
    "kleinanzeigen": {
      "command": "C:\\path\\to\\.venv\\Scripts\\python.exe",
      "args": ["-m", "kleinanzeigen_mcp.server"]
    }
  }
}
```

Restart Claude Desktop and test: **"Search for laptops in Berlin"**

## � Usage

### Run Server
```powershell
# With uv
uv run kleinanzeigen-mcp

# Or activate venv
.\.venv\Scripts\Activate.ps1
python -m kleinanzeigen_mcp.server
```

### Development
```powershell
# Run tests
uv run pytest

# Debug mode
$env:LOG_LEVEL="DEBUG"
uv run kleinanzeigen-mcp
```

## 🔧 Troubleshooting

### UV not found
```powershell
# Refresh PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
```

### Playwright fails
```powershell
.\.venv\Scripts\playwright.exe install chromium --with-deps
```

### Claude doesn't see tools
1. Check config path: `%APPDATA%\Claude\claude_desktop_config.json`
2. Verify Python path is absolute
3. Restart Claude Desktop

## 🛠️ Tools Available

- **search_listings** - Search with filters (query, location, price)
- **get_listing_details** - Get full info for a listing

## 🐳 Docker Alternative

```powershell
docker compose --profile stdio up -d kleinanzeigen-mcp
```

## 📚 More Info

See `README.MD` for full documentation.

---

**Status:** Run `.\setup-uv.ps1` to get started! 🚀
