# Kleinanzeigen MCP Server - Installation & Setup Script (UV Version)
# Run this script in PowerShell to set up everything using uv

Write-Host "🚀 Kleinanzeigen MCP Server - Setup (UV)" -ForegroundColor Cyan
Write-Host "==========================================`n" -ForegroundColor Cyan

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found! Please install Python 3.11 or higher." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green

# Check if UV is installed
Write-Host "`nChecking for uv..." -ForegroundColor Yellow
$uvCheck = uv --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  uv not found. Installing uv..." -ForegroundColor Yellow
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    $uvCheck = uv --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install uv. Please install manually from https://docs.astral.sh/uv/" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ uv installed: $uvCheck" -ForegroundColor Green
} else {
    Write-Host "✓ uv found: $uvCheck" -ForegroundColor Green
}

# Create virtual environment with uv
Write-Host "`n📦 Creating virtual environment..." -ForegroundColor Yellow
uv venv

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Virtual environment created" -ForegroundColor Green

# Install dependencies
Write-Host "`n📦 Installing dependencies..." -ForegroundColor Yellow
uv pip install -e ".[dev]"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Install Playwright browser
Write-Host "`n🌐 Installing Playwright browser (Chromium)..." -ForegroundColor Yellow

# Activate virtual environment and install playwright
& .\.venv\Scripts\playwright.exe install chromium

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Playwright installation had issues, but may still work" -ForegroundColor Yellow
} else {
    Write-Host "✓ Playwright browser installed" -ForegroundColor Green
}

# Install Playwright system dependencies
Write-Host "`n🔧 Installing Playwright system dependencies..." -ForegroundColor Yellow
& .\.venv\Scripts\playwright.exe install-deps chromium

# Test the installation
Write-Host "`n🧪 Testing MCP server..." -ForegroundColor Yellow
Write-Host "Starting server for 5 seconds to verify..." -ForegroundColor Gray

$job = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    & .\.venv\Scripts\python.exe -m kleinanzeigen_mcp.server
}

Start-Sleep -Seconds 5

if ($job.State -eq "Running") {
    Write-Host "✓ MCP server started successfully!" -ForegroundColor Green
    Stop-Job $job
    Remove-Job $job
} else {
    Write-Host "⚠️  Server test inconclusive - check logs manually" -ForegroundColor Yellow
    Remove-Job $job
}

# Generate Claude Desktop config template
Write-Host "`n📋 Generating Claude Desktop configuration template..." -ForegroundColor Yellow

$currentPath = (Get-Location).Path.Replace('\', '\\')
$pythonPath = Join-Path $currentPath ".venv\\Scripts\\python.exe"
$pythonPath = $pythonPath.Replace('\', '\\')

$configJson = @"
{
  "mcpServers": {
    "kleinanzeigen": {
      "command": "$pythonPath",
      "args": ["-m", "kleinanzeigen_mcp.server"],
      "cwd": "$currentPath"
    }
  }
}
"@

$configPath = "claude_desktop_config.example.generated.json"
$configJson | Out-File -FilePath $configPath -Encoding UTF8
Write-Host "✓ Config template saved to: $configPath" -ForegroundColor Green

Write-Host "`n╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🎉 Installation Complete!                            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

Write-Host "`n📝 Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Copy configuration to Claude Desktop:" -ForegroundColor White
Write-Host "     Location: %APPDATA%\Claude\claude_desktop_config.json" -ForegroundColor Gray
Write-Host "     Template: $configPath" -ForegroundColor Gray
Write-Host "     ⚠️  IMPORTANT: Adjust the paths if needed!" -ForegroundColor Yellow
Write-Host "`n  2. Restart Claude Desktop" -ForegroundColor White
Write-Host "`n  3. Test with: 'Search for laptops in Berlin under 500€'" -ForegroundColor White

Write-Host "`n🚀 Quick Start Commands:" -ForegroundColor Yellow
Write-Host "  Activate venv: .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  Run server:    .\.venv\Scripts\python.exe -m kleinanzeigen_mcp.server" -ForegroundColor White
Write-Host "  Run with uv:   uv run kleinanzeigen-mcp" -ForegroundColor White
Write-Host "  Run tests:     uv run pytest" -ForegroundColor White
Write-Host "  With Docker:   docker compose --profile stdio up" -ForegroundColor White

Write-Host "`n📚 Documentation: See START_HERE.md for details" -ForegroundColor Cyan
Write-Host ""
