# Server-side Deployment Guide

This guide explains how to deploy the Kleinanzeigen MCP Server on a remote server with **SSE transport**, making it accessible from all your clients (Claude Desktop, mobile apps, etc.) via HTTPS.

## Architecture Overview

```
┌─────────────┐
│   Clients   │  (Claude Desktop, Mobile, etc.)
│ (anywhere)  │
└──────┬──────┘
       │ HTTPS/SSE
       ▼
┌─────────────┐
│   Traefik   │  (Reverse Proxy, HTTPS, Rate Limiting)
│   :443      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ MCP Server  │  (SSE Transport Mode)
│   :8000     │
└─────────────┘
```

## Prerequisites

1. **Linux server** with:
   - Docker & Docker Compose installed
   - Public IP address
   - Ports 80 & 443 open in firewall

2. **Domain name** with DNS A record pointing to your server IP
   - Example: `mcp.yourdomain.com` → `123.45.67.89`

3. **Email address** for Let's Encrypt certificate notifications

## Installation Steps

### 1. Clone Repository on Server

```bash
cd /opt
sudo git clone https://github.com/yourusername/ebay-kleinanzeigen-api-mcp.git
cd ebay-kleinanzeigen-api-mcp
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.server.example .env.server

# Generate secure API key
openssl rand -hex 32

# Edit configuration
nano .env.server
```

Fill in these values:
```env
MCP_DOMAIN=mcp.yourdomain.com
ACME_EMAIL=your-email@example.com
MCP_API_KEY=<paste-your-generated-key>
GRAFANA_PASSWORD=<optional-if-using-monitoring>
```

### 3. Build Docker Image

```bash
# Build the MCP server image
docker build -f Dockerfile.mcp -t kleinanzeigen-mcp:latest .
```

### 4. Start Services

**Basic deployment (without monitoring):**
```bash
docker-compose -f docker-compose.server.yml --env-file .env.server up -d
```

**With monitoring (Prometheus + Grafana):**
```bash
docker-compose -f docker-compose.server.yml --env-file .env.server --profile monitoring up -d
```

### 5. Verify Deployment

```bash
# Check running containers
docker-compose -f docker-compose.server.yml ps

# Check MCP server logs
docker-compose -f docker-compose.server.yml logs kleinanzeigen-mcp

# Check Traefik logs
docker-compose -f docker-compose.server.yml logs traefik

# Test SSE endpoint
curl https://mcp.yourdomain.com/sse
```

## Client Configuration

### Claude Desktop (Windows/Mac)

Edit your Claude Desktop config:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "kleinanzeigen": {
      "url": "https://mcp.yourdomain.com/sse",
      "transport": "sse",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY_HERE"
      }
    }
  }
}
```

### Claude Mobile (via Claude Desktop sync)

Claude Desktop config automatically syncs to mobile apps. No additional configuration needed.

### Other MCP Clients

For clients supporting SSE transport:
- **Endpoint:** `https://mcp.yourdomain.com/sse`
- **Transport:** SSE
- **Authentication:** `Authorization: Bearer <your-api-key>`

## Security Considerations

### 1. API Key Protection
- **Never commit** `.env.server` to Git
- Use strong random keys (32+ characters)
- Rotate keys regularly
- Use different keys for dev/prod

### 2. Rate Limiting
Current configuration: **100 requests/minute per IP**

Adjust in `docker-compose.server.yml`:
```yaml
- traefik.http.middlewares.mcp-ratelimit.ratelimit.average=100
- traefik.http.middlewares.mcp-ratelimit.ratelimit.period=1m
```

### 3. Firewall Rules
```bash
# Allow HTTP (for Let's Encrypt challenge)
sudo ufw allow 80/tcp

# Allow HTTPS
sudo ufw allow 443/tcp

# Block direct access to MCP port
sudo ufw deny 8000/tcp
```

### 4. HTTPS/TLS
- Let's Encrypt certificates auto-renew via Traefik
- Certificates stored in Docker volume `traefik-letsencrypt`
- Automatic HTTP → HTTPS redirect

## Monitoring (Optional)

If started with `--profile monitoring`:

### Prometheus
- **URL:** `http://your-server-ip:9090`
- Metrics: Request rates, latencies, errors
- Retention: 15 days (default)

### Grafana
- **URL:** `http://your-server-ip:3000`
- **User:** `admin`
- **Password:** From `.env.server` (GRAFANA_PASSWORD)

Import MCP dashboard:
1. Login to Grafana
2. Configuration → Data Sources → Add Prometheus
3. URL: `http://prometheus:9090`
4. Dashboards → Import → Upload `monitoring/mcp-dashboard.json`

## Maintenance

### Update Server

```bash
# Pull latest changes
git pull

# Rebuild image
docker build -f Dockerfile.mcp -t kleinanzeigen-mcp:latest .

# Restart services (zero-downtime with Traefik)
docker-compose -f docker-compose.server.yml --env-file .env.server up -d --force-recreate kleinanzeigen-mcp
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.server.yml logs -f

# Specific service
docker-compose -f docker-compose.server.yml logs -f kleinanzeigen-mcp

# Last 100 lines
docker-compose -f docker-compose.server.yml logs --tail=100 kleinanzeigen-mcp
```

### Backup

```bash
# Backup Let's Encrypt certificates
sudo docker run --rm \
  -v $(pwd)/backups:/backup \
  -v ebay-kleinanzeigen-api-mcp_traefik-letsencrypt:/data \
  alpine tar czf /backup/letsencrypt-$(date +%Y%m%d).tar.gz -C /data .

# Backup monitoring data (if using)
sudo docker run --rm \
  -v $(pwd)/backups:/backup \
  -v ebay-kleinanzeigen-api-mcp_prometheus-data:/prometheus \
  -v ebay-kleinanzeigen-api-mcp_grafana-data:/grafana \
  alpine tar czf /backup/monitoring-$(date +%Y%m%d).tar.gz \
    -C /prometheus . -C /grafana .
```

### Stop Services

```bash
# Stop all
docker-compose -f docker-compose.server.yml down

# Stop and remove volumes (CAUTION: deletes certificates!)
docker-compose -f docker-compose.server.yml down -v
```

## Troubleshooting

### Let's Encrypt Certificate Fails

**Error:** `acme: error: 400 :: urn:ietf:params:acme:error:connection`

**Solutions:**
1. Verify DNS record: `dig mcp.yourdomain.com`
2. Check ports 80 & 443 are accessible: `telnet your-server-ip 80`
3. Wait 5 minutes after DNS changes (propagation time)
4. Check Traefik logs: `docker-compose -f docker-compose.server.yml logs traefik`

### MCP Server Not Starting

**Check logs:**
```bash
docker-compose -f docker-compose.server.yml logs kleinanzeigen-mcp
```

**Common issues:**
- Missing environment variables → Check `.env.server`
- Port 8000 already in use → `lsof -i :8000`
- Insufficient memory → Increase Docker limits

### Client Connection Issues

**Test endpoint manually:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://mcp.yourdomain.com/sse
```

**Expected response:** SSE stream connection

**Common issues:**
- Wrong API key → Verify in `.env.server` and client config
- DNS not resolving → Check with `nslookup mcp.yourdomain.com`
- Firewall blocking → Test from different network
- Rate limit exceeded → Check Traefik logs

## Performance Tuning

### Resource Limits

Edit `docker-compose.server.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'          # Max CPU cores
      memory: 2G           # Max RAM
    reservations:
      cpus: '0.5'          # Min guaranteed CPU
      memory: 512M         # Min guaranteed RAM
```

### Playwright Performance

Chromium can be memory-intensive. Monitor usage:
```bash
docker stats kleinanzeigen-mcp
```

Consider adding swap if RAM < 2GB:
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Advanced Configuration

### Custom Domain per Tool

To run multiple MCP servers on same server:

```yaml
# In docker-compose.server.yml
kleinanzeigen-mcp:
  labels:
    - traefik.http.routers.kleinanzeigen-mcp.rule=Host(`kleinanzeigen.yourdomain.com`)

another-mcp:
  labels:
    - traefik.http.routers.another-mcp.rule=Host(`other.yourdomain.com`)
```

### IP Allowlist

Restrict access to specific IPs:

```yaml
# In docker-compose.server.yml
labels:
  - traefik.http.middlewares.mcp-ipallowlist.ipallowlist.sourcerange=1.2.3.4/32,5.6.7.0/24
  - traefik.http.routers.kleinanzeigen-mcp.middlewares=mcp-ipallowlist@docker
```

### Custom Rate Limits per Client

Use different middleware for different clients:

```yaml
# Fast lane for trusted clients
- traefik.http.middlewares.mcp-ratelimit-fast.ratelimit.average=1000
- traefik.http.middlewares.mcp-ratelimit-fast.ratelimit.period=1m

# Slow lane for others
- traefik.http.middlewares.mcp-ratelimit-slow.ratelimit.average=10
- traefik.http.middlewares.mcp-ratelimit-slow.ratelimit.period=1m
```

## Support

- **Issues:** https://github.com/yourusername/ebay-kleinanzeigen-api-mcp/issues
- **Discussions:** https://github.com/yourusername/ebay-kleinanzeigen-api-mcp/discussions
- **Original Fork:** https://github.com/DanielWTE/ebay-kleinanzeigen-api

## License

MIT License - See LICENSE file for details
