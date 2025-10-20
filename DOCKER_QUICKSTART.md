# ⚡ Quick Start - Kleinanzeigen MCP Server mit Docker Desktop

Richte den Kleinanzeigen MCP Server in **unter 5 Minuten** ein!

## Voraussetzungen (30 Sekunden)

✅ **Docker Desktop** installiert und läuft  
✅ **Claude Desktop** installiert  
✅ Terminal/PowerShell geöffnet  

## Schritt 1: Docker MCP Toolkit aktivieren (1 Minute)

1. Öffne **Docker Desktop**
2. Gehe zu **Settings** → **Beta Features**
3. Aktiviere **"Docker MCP Toolkit"**
4. Klicke **Apply & Restart**

## Schritt 2: Docker Image bauen (2 Minuten)

```powershell
# Repository klonen (oder ZIP herunterladen)
git clone https://github.com/DEIN_USERNAME/ebay-kleinanzeigen-api-mcp.git
cd ebay-kleinanzeigen-api-mcp

# Docker Image bauen (dauert ~2 Minuten wegen Playwright)
docker build -t kleinanzeigen-mcp:latest -f Dockerfile.mcp .
```

## Schritt 3: Custom Catalog erstellen (1 Minute)

### Windows (PowerShell):
```powershell
# Catalogs-Verzeichnis erstellen
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.docker\mcp\catalogs"

# Custom catalog erstellen
@"
version: 2
name: custom
displayName: Custom MCP Servers
registry:
  kleinanzeigen:
    description: "Search and browse listings on kleinanzeigen.de (formerly eBay Kleinanzeigen)"
    title: "Kleinanzeigen Search"
    type: server
    dateAdded: "2025-01-20T00:00:00Z"
    image: kleinanzeigen-mcp:latest
    ref: ""
    tools:
      - name: search_listings
        description: Search listings with filters (location, price, radius)
      - name: get_listing_details
        description: Get complete details for a specific listing
    prompts:
      - name: find_deals
        description: Find deals within budget
      - name: compare_listings
        description: Compare multiple listings
      - name: monitor_search
        description: Monitor search results
    metadata:
      category: productivity
      tags:
        - shopping
        - search
        - marketplace
        - germany
"@ | Out-File -FilePath "$env:USERPROFILE\.docker\mcp\catalogs\custom.yaml" -Encoding UTF8
```

### macOS/Linux (Bash):
```bash
# Catalogs-Verzeichnis erstellen
mkdir -p ~/.docker/mcp/catalogs

# Custom catalog erstellen
cat > ~/.docker/mcp/catalogs/custom.yaml << 'EOF'
version: 2
name: custom
displayName: Custom MCP Servers
registry:
  kleinanzeigen:
    description: "Search and browse listings on kleinanzeigen.de (formerly eBay Kleinanzeigen)"
    title: "Kleinanzeigen Search"
    type: server
    dateAdded: "2025-01-20T00:00:00Z"
    image: kleinanzeigen-mcp:latest
    ref: ""
    tools:
      - name: search_listings
        description: Search listings with filters (location, price, radius)
      - name: get_listing_details
        description: Get complete details for a specific listing
    prompts:
      - name: find_deals
        description: Find deals within budget
      - name: compare_listings
        description: Compare multiple listings
      - name: monitor_search
        description: Monitor search results
    metadata:
      category: productivity
      tags:
        - shopping
        - search
        - marketplace
        - germany
EOF
```

## Schritt 4: Registry aktualisieren (30 Sekunden)

### Windows (PowerShell):
```powershell
# Registry-Datei erstellen/aktualisieren
@"
  kleinanzeigen:
    ref: ""
"@ | Add-Content -Path "$env:USERPROFILE\.docker\mcp\registry.yaml"
```

### macOS/Linux (Bash):
```bash
# Registry aktualisieren
echo "  kleinanzeigen:" >> ~/.docker/mcp/registry.yaml
echo '    ref: ""' >> ~/.docker/mcp/registry.yaml
```

## Schritt 5: Claude Desktop konfigurieren (1 Minute)

### Windows:
```powershell
notepad "$env:APPDATA\Claude\claude_desktop_config.json"
```

### macOS:
```bash
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Konfiguration hinzufügen** (ersetze `[IHR_USERNAME]` mit deinem Benutzernamen):

### Windows:
```json
{
  "mcpServers": {
    "mcp-toolkit-gateway": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "-v", "C:\\Users\\[IHR_USERNAME]\\.docker\\mcp:/mcp",
        "docker/mcp-gateway",
        "--catalog=/mcp/catalogs/docker-mcp.yaml",
        "--catalog=/mcp/catalogs/custom.yaml",
        "--config=/mcp/config.yaml",
        "--registry=/mcp/registry.yaml",
        "--tools-config=/mcp/tools.yaml",
        "--transport=stdio"
      ]
    }
  }
}
```

### macOS/Linux:
```json
{
  "mcpServers": {
    "mcp-toolkit-gateway": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "-v", "/Users/[IHR_USERNAME]/.docker/mcp:/mcp",
        "docker/mcp-gateway",
        "--catalog=/mcp/catalogs/docker-mcp.yaml",
        "--catalog=/mcp/catalogs/custom.yaml",
        "--config=/mcp/config.yaml",
        "--registry=/mcp/registry.yaml",
        "--tools-config=/mcp/tools.yaml",
        "--transport=stdio"
      ]
    }
  }
}
```

**⚠️ Wichtig:** Doppelte Backslashes unter Windows: `C:\\Users\\...`

## Schritt 6: Testen! (30 Sekunden)

1. **Claude Desktop komplett beenden** und neu starten
2. Neuen Chat öffnen
3. Tools-Icon klicken (oder Cmd/Ctrl+I)
4. Du solltest **"mcp-toolkit-gateway"** mit Kleinanzeigen-Tools sehen
5. Teste es: **"Suche nach Laptops in Berlin unter 500€"**

## 🎉 Fertig!

Claude kann jetzt Kleinanzeigen.de durchsuchen!

## Beispiel-Anfragen

```
"Finde Fahrräder in München unter 300€"
"Zeige mir Gaming-PCs in 10178 (Berlin Mitte)"
"Suche nach Sofas im Umkreis von 20km von Stuttgart"
```

## Fehlerbehebung

**Tools erscheinen nicht?**
- Docker Desktop läuft?
- Image erfolgreich gebaut? → `docker images | grep kleinanzeigen`
- Claude Logs prüfen: Help → Show Logs

**Permission Errors?**
- Docker Desktop hat nötige Rechte?
- Windows: Docker als Administrator?

**Container startet nicht?**
```powershell
# Logs checken
docker logs mcp-toolkit-gateway
```

**Noch Probleme?**
- Siehe [README.md](README.MD) für detaillierte Dokumentation
- Oder verwende die lokale Installation: [START_HERE.md](START_HERE.md)

## Alternative: Lokale Installation (ohne Docker)

Wenn Docker Probleme macht, verwende die UV-Installation:

```powershell
# Siehe START_HERE.md für vollständige Anleitung
.\setup-uv.ps1
```

---

💡 **Tipp:** Der Server läuft in Docker, daher sind keine lokalen Python-Abhängigkeiten nötig!
