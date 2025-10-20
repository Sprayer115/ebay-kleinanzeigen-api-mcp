# Server-side Deployment Guide

This guide explains how to deploy the Kleinanzeigen MCP Server on a remote server with **SSE transport**, making it accessible from all your clients (Claude Desktop, mobile apps, etc.) via HTTPS.

**This guide assumes you already have a reverse proxy** (Nginx Proxy Manager, Traefik, Caddy, Cloudflare Tunnel, etc.) that handles HTTPS/SSL. The MCP server runs on HTTP port 8000 and your reverse proxy forwards HTTPS traffic to it.

## Architecture Overview

```
┌─────────────┐
│   Clients   │  (Claude Desktop, Mobile, etc.)
│ (anywhere)  │
└──────┬──────┘
       │ HTTPS/SSE
       ▼
┌─────────────┐
│   Cloudflare│  (Optional: DDoS protection, CDN)
│   + Your    │
│ Reverse Proxy│  (Nginx Proxy Manager, Traefik, Caddy, etc.)
│   :443      │  (Handles: SSL/TLS, Rate Limiting, Auth)
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐
│ MCP Server  │  (SSE Transport Mode)
│   :8000     │
└─────────────┘
```

## Prerequisites

1. **Linux server** with:
   - Docker & Docker Compose installed
   - Public IP address or accessible via VPN/tunnel

2. **Reverse Proxy** already configured:
   - Nginx Proxy Manager (recommended for beginners)
   - Traefik, Caddy, or similar
   - Cloudflare Tunnel (for remote access without open ports)

3. **Domain name** (optional but recommended):
   - Example: `mcp.yourdomain.com`
   - Can also use IP address for testing

## Installation Steps

### 1. Clone Repository on Server

```bash
cd /opt  # or your preferred location
sudo git clone https://github.com/Sprayer115/ebay-kleinanzeigen-api-mcp.git
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
MCP_API_KEY=<paste-your-generated-key>
MCP_PORT=8000
LOG_LEVEL=INFO
```

### 3. Build Docker Image

```bash
# Build the MCP server image
docker build -f Dockerfile.mcp -t kleinanzeigen-mcp:latest .
```

### 4. Start MCP Server

**Basic deployment:**

```bash
docker-compose -f docker-compose.server.yml --env-file .env.server up -d
```

**With monitoring (Prometheus + Grafana):**

```bash
docker-compose -f docker-compose.server.yml --env-file .env.server --profile monitoring up -d
```

### 5. Configure Your Reverse Proxy

Now configure your reverse proxy to forward HTTPS traffic to the MCP server.

#### Option A: Nginx Proxy Manager (Recommended)

1. **Login to Nginx Proxy Manager**
2. **Go to: Proxy Hosts → Add Proxy Host**

```
Domain Names: mcp.yourdomain.com
Scheme: http
Forward Hostname/IP: <your-server-ip or localhost>
Forward Port: 8000

✓ Block Common Exploits
✓ Websockets Support (CRITICAL for SSE!)
```

3. **SSL Tab:**

```
✓ Force SSL
✓ HTTP/2 Support
✓ HSTS Enabled

SSL Certificate: Request a new SSL Certificate with Let's Encrypt
or use existing Cloudflare certificate
```

4. **Advanced Tab (Optional - for rate limiting):**

```nginx
# Rate limiting (100 requests per minute)
limit_req_zone $binary_remote_addr zone=mcp_limit:10m rate=100r/m;
limit_req zone=mcp_limit burst=20 nodelay;

# SSE configuration
proxy_buffering off;
proxy_cache off;
proxy_read_timeout 86400;
proxy_http_version 1.1;
```

#### Option B: Traefik (if you already use it)

Create a `traefik-labels.yml` or add to existing config:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.mcp.rule=Host(`mcp.yourdomain.com`)"
  - "traefik.http.routers.mcp.entrypoints=websecure"
  - "traefik.http.routers.mcp.tls.certresolver=letsencrypt"
  - "traefik.http.services.mcp.loadbalancer.server.port=8000"
```

#### Option C: Cloudflare Tunnel (Zero Trust)

```bash
# Install cloudflared
# See: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/

cloudflared tunnel create mcp-tunnel
cloudflared tunnel route dns mcp-tunnel mcp.yourdomain.com

# Add to config.yml:
tunnel: <tunnel-id>
credentials-file: /root/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: mcp.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

### 6. Verify Deployment

```bash
# Check running containers
docker-compose -f docker-compose.server.yml ps

# Check MCP server logs
docker-compose -f docker-compose.server.yml logs kleinanzeigen-mcp

# Test endpoint (from server)
curl http://localhost:8000/sse

# Test via domain (from outside)
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

Configure in your reverse proxy (Nginx, Traefik, etc.)

**Nginx example:**

```nginx
limit_req_zone $binary_remote_addr zone=mcp_limit:10m rate=100r/m;
limit_req zone=mcp_limit burst=20 nodelay;
```

**Traefik example:**

```yaml
- traefik.http.middlewares.mcp-ratelimit.ratelimit.average=100
- traefik.http.middlewares.mcp-ratelimit.ratelimit.period=1m
```

### 3. Firewall Rules

```bash
# If using direct port exposure (not Cloudflare Tunnel):

# Allow your reverse proxy port (usually handled by reverse proxy)
sudo ufw allow 443/tcp

# Block direct access to MCP port
sudo ufw deny 8000/tcp

# Or only allow from localhost/docker network
sudo ufw allow from 172.16.0.0/12 to any port 8000
```

### 4. HTTPS/TLS

- Configure SSL in your reverse proxy (Nginx Proxy Manager, Traefik, etc.)
- Use Let's Encrypt for free automatic certificates
- Enable HSTS, HTTP/2
- For Cloudflare: Use "Full (strict)" SSL mode

### 5. Cloudflare Protection (Optional but Recommended)

If using Cloudflare:

1. **DNS:** Proxy enabled (orange cloud)
2. **SSL/TLS:** Full (strict)
3. **Firewall Rules:** Restrict to your IP or country
4. **Rate Limiting:** Additional protection at CDN level
5. **DDoS Protection:** Automatic

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

### SSL/Certificate Issues

**Problem:** SSL certificate errors in client

**Solutions:**

1. Verify your reverse proxy has valid SSL certificate
2. Check domain DNS: `dig mcp.yourdomain.com`
3. Test SSL: `curl -v https://mcp.yourdomain.com/sse`
4. For Cloudflare: Use "Full (strict)" SSL mode
5. Check reverse proxy logs

### MCP Server Not Starting

**Check logs:**

```bash
docker-compose -f docker-compose.server.yml logs kleinanzeigen-mcp
```

**Common issues:**

- Missing environment variables → Check `.env.server`
- Port 8000 already in use → `lsof -i :8000` or `netstat -tulpn | grep 8000`
- Insufficient memory → Increase Docker limits
- Image not built → Run `docker build -f Dockerfile.mcp -t kleinanzeigen-mcp:latest .`

### Client Connection Issues

**Test endpoint manually:**

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://mcp.yourdomain.com/sse
```

**Expected response:** SSE stream connection starts

**Common issues:**

- **502 Bad Gateway:**
  - MCP server not running → Check logs
  - Wrong port in reverse proxy → Should forward to port 8000
  - Websockets not enabled → Enable in reverse proxy config
  
- **Wrong API key:** Verify in `.env.server` and client config
- **DNS not resolving:** Check with `nslookup mcp.yourdomain.com`
- **Firewall blocking:** Test from different network
- **Reverse proxy misconfigured:** Check proxy logs

### Websockets/SSE Not Working

**This is the most common issue!**

**For Nginx Proxy Manager:**

1. ✓ Enable "Websockets Support" in proxy host config
2. Add custom config:

```nginx
proxy_buffering off;
proxy_cache off;
proxy_http_version 1.1;
```

**For Traefik:**

Traefik handles WebSockets automatically, no special config needed.

**For Cloudflare:**

WebSockets work automatically with proxied domains (orange cloud).

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
