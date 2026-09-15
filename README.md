# ProxyBox - Remote Browser with Traffic Interception

**Architecture: Chromium Standalone + CDP + Playwright + Mitmproxy**

ProxyBox is a Docker-based remote browser system that allows you to control a Chromium browser instance through Chrome DevTools Protocol (CDP) and intercept/modify HTTP/HTTPS traffic using Mitmproxy. Designed for integration with WPF applications or any remote client.

## 🎯 Features

- **Chromium Standalone**: Browser runs as an independent process inside Docker
- **CDP Control**: Full browser automation via Chrome DevTools Protocol
- **Persistent Sessions**: User data directory survives container restarts
- **Traffic Interception**: Mitmproxy for HTTP/HTTPS request/response manipulation
- **Custom DNS Routing**: Dynamic DNS routes (e.g., `ilmiosito.com` → `10.58.54.2`)
- **Web Dashboard**: HTML-based browser control interface
- **WPF Integration**: Connect from WPF applications via REST API
- **No Local Chromium**: Browser binaries are inside Docker, not on local machine

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        PROXYBOX (Docker)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   CONTROL PLANE                    BROWSER LAYER              │
│   ─────────────                    ────────────              │
│      Flask API :5000 ────────────▶ Chromium :9222 (CDP)     │
│          │                              │                         │
│          │ CDP Connection                │                         │
│          ▼                              ▼                         │
│   BrowserManager ─────────────────▶ Playwright                │
│          │                              │                         │
│   NETWORK LAYER:                 │                         │
│   ─────────────                  │                         │
│      DNS Manager ─────────────────┘                         │
│          │                                              │
│          ▼                                              │
│      Mitmproxy :8080 ──────────────────────────────▶ INTERNET│
│                                                             │
└─────────────────────────────────────────────────────────────┘
         ▲
         │ HTTPS
         │
    WPF Client (Locale)
```

### Component Responsibilities

- **BrowserManager**: Manages Chromium process lifecycle, page creation, navigation, content operations
- **ProxyManager**: Manages Mitmproxy process lifecycle
- **DNSManager**: Manages DNS routes (in-memory), integrates with Mitmproxy addon
- **MitmproxyAddon**: Handles traffic interception, DNS routing application, logging
- **Flask API**: Control plane that coordinates all components

## 📁 Project Structure

```
proxybox/
├── Dockerfile.render          # Docker configuration for Render.com
├── docker-compose.yml         # Local development configuration
├── .env.example               # Environment variables template
├── README.md                  # This file
│
├── api/
│   ├── app.py                 # Flask API - Control Plane
│   ├── browser/
│   │   ├── __init__.py
│   │   ├── chromium.py         # Chromium process management
│   │   └── manager.py         # Browser session management
│   ├── network/
│   │   ├── __init__.py
│   │   ├── dns_manager.py     # DNS route management
│   │   └── proxy_manager.py   # Mitmproxy process management
│   ├── mitmproxy/
│   │   ├── __init__.py
│   │   └── addon.py           # Mitmproxy traffic handler
│   └── templates/
│       └── index.html         # Web dashboard
│
├── scripts/
│   ├── start.sh               # Main startup orchestrator
│   └── start-chromium.sh      # Chromium startup script
│
└── data/
    └── chromium/               # Persistent browser data (volume)
```

## 🚀 Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/Jack96BO/proxybox.git
cd proxybox

# Copy environment variables
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Build and Run with Docker Compose (Development)

```bash
# Build the image
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 3. Access Services

- **Web Dashboard**: http://localhost:5000
- **Flask API**: http://localhost:5000/api/
- **Mitmproxy**: http://localhost:8080
- **Chromium CDP**: http://localhost:9222 (internal only)

## 📡 API Endpoints

### Browser Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/browser/status` | Get browser status |
| POST | `/api/browser/start` | Start browser |
| POST | `/api/browser/stop` | Stop browser |
| POST | `/api/browser/restart` | Restart browser |
| POST | `/api/browser/page` | Create new page |
| GET | `/api/browser/pages` | List all pages |
| POST | `/api/browser/navigate` | Navigate to URL |
| POST | `/api/browser/screenshot` | Take screenshot |
| POST | `/api/browser/html` | Get page HTML |
| POST | `/api/browser/text` | Get page text |
| POST | `/api/browser/js` | Execute JavaScript |
| POST | `/api/browser/click` | Click element |
| POST | `/api/browser/fill` | Fill form field |

### DNS Routing

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dns/routes` | List all DNS routes |
| POST | `/api/dns/routes` | Add new DNS route |
| DELETE | `/api/dns/routes/<domain>` | Remove DNS route |
| DELETE | `/api/dns/routes` | Clear all routes |

### Proxy Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/proxy/status` | Get proxy status |
| POST | `/api/proxy/start` | Start proxy |
| POST | `/api/proxy/stop` | Stop proxy |
| POST | `/api/proxy/restart` | Restart proxy |

### Traffic Statistics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stats` | Get traffic statistics |
| POST | `/api/stats/reset` | Reset statistics |

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_PORT` | 5000 | Flask API port |
| `MITMPROXY_PORT` | 8080 | Mitmproxy port |
| `CDP_PORT` | 9222 | Chromium CDP port |
| `PROXY_SERVER` | http://127.0.0.1:8080 | Proxy server URL |
| `USER_DATA_DIR` | /data/chromium | Chromium user data directory |

### Docker Configuration

The `Dockerfile.render` is optimized for Render.com deployment:

- Installs Chromium system package
- Installs Playwright and Mitmproxy
- Configures persistent volume for `/data/chromium`
- Exposes ports 5000 (API), 8080 (Proxy), 9222 (CDP - internal only)

## 🎨 Web Dashboard

The dashboard at http://localhost:5000 provides:

- **Browser Control**: Start/stop browser, create pages, navigate
- **DNS Management**: Add/remove custom DNS routes
- **Proxy Control**: Start/stop Mitmproxy
- **Traffic Viewer**: View intercepted requests/responses
- **JavaScript Execution**: Run custom JS on pages
- **Screenshot Capture**: Capture and view page screenshots
- **Page Inspector**: View HTML, text content, click elements

## 🔄 WPF Integration

Your WPF application can connect to ProxyBox via HTTP API:

```csharp
// Example: Create a new browser page
var client = new HttpClient();
var response = await client.PostAsync(
    "http://your-proxybox-url/api/browser/page",
    new StringContent("{\"url\": \"https://google.com\"}", Encoding.UTF8, "application/json")
);

// Example: Navigate to URL
var navigateResponse = await client.PostAsync(
    "http://your-proxybox-url/api/browser/navigate",
    new StringContent("{\"page_id\": \"page_1\", \"url\": \"https://example.com\"}", Encoding.UTF8, "application/json")
);

// Example: Execute JavaScript
var jsResponse = await client.PostAsync(
    "http://your-proxybox-url/api/browser/js",
    new StringContent("{\"page_id\": \"page_1\", \"code\": \"console.log('Hello from WPF!')\"}", Encoding.UTF8, "application/json")
);
```

## 🔒 Security Considerations

- **CDP Port**: Only bound to `127.0.0.1:9222` - never exposed externally
- **HTTPS Interception**: Mitmproxy uses `--ssl-insecure` for development
- **Chromium**: Uses `--ignore-certificate-errors` for Mitmproxy compatibility
- **No Authentication**: API has no auth by default (add for production)

## 📊 Custom DNS Routing

Add custom DNS routes dynamically without fixed IP addresses:

```bash
# Add a route
curl -X POST http://localhost:5000/api/dns/routes \
  -H "Content-Type: application/json" \
  -d '{"domain": "ilmiosito.com", "ip": "10.58.54.2"}'

# List all routes
curl http://localhost:5000/api/dns/routes

# Remove a route
curl -X DELETE http://localhost:5000/api/dns/routes/ilmiosito.com

# Clear all routes
curl -X DELETE http://localhost:5000/api/dns/routes
```

## 🐳 Deploy to Render.com

1. Create a new **Web Service** on Render.com
2. Connect your GitHub repository
3. Configure:
   - **Dockerfile Path**: `Dockerfile.render`
   - **Branch**: `main`
   - **Region**: Oregon (or your preferred region)
   - **Compute Plan**: Free or paid (free spins down after inactivity)
4. Add Environment Variables:
   - `FLASK_PORT=5000`
   - `MITMPROXY_PORT=8080`
   - `CDP_PORT=9222`
   - `PROXY_SERVER=http://127.0.0.1:8080`
5. Deploy!

**Note**: For persistent storage on Render, enable **Persistent Disk** and mount it to `/data/chromium`.

## 🧪 Testing

### Test Browser Functionality

```bash
# Start browser
curl -X POST http://localhost:5000/api/browser/start

# Create page
curl -X POST http://localhost:5000/api/browser/page \
  -H "Content-Type: application/json" \
  -d '{"url": "https://google.com"}'

# Take screenshot
curl -X POST http://localhost:5000/api/browser/screenshot \
  -H "Content-Type: application/json" \
  -d '{"page_id": "page_1"}'
```

### Test DNS Routing

```bash
# Add route
curl -X POST http://localhost:5000/api/dns/routes \
  -H "Content-Type: application/json" \
  -d '{"domain": "example.com", "ip": "93.184.216.34"}'

# Navigate to routed domain
curl -X POST http://localhost:5000/api/browser/navigate \
  -H "Content-Type: application/json" \
  -d '{"page_id": "page_1", "url": "https://example.com"}'
```

## 📝 Architecture Details

### Chromium Configuration

Chromium runs as standalone process with:
```bash
chromium \
  --remote-debugging-port=9222 \
  --user-data-dir=/data/chromium \
  --headless=new \
  --proxy-server=http://127.0.0.1:8080 \
  --no-sandbox \
  --disable-setuid-sandbox \
  --disable-gpu \
  --ignore-certificate-errors
```

### Playwright Connection

Playwright connects to existing Chromium via CDP:
```python
browser = await playwright.chromium.connect_over_cdp("http://127.0.0.1:9222")
```

### Service Orchestration

The `start.sh` script starts services in order:
1. Mitmproxy (port 8080)
2. Chromium standalone (port 9222 CDP)
3. Flask API (port 5000)

## 🎯 Future Enhancements

- **AI Agents**: Add AI-powered browser automation
- **Multi-Browser**: Support multiple Chromium instances
- **Browser Contexts**: Isolated browsing sessions
- **WebSocket API**: Real-time browser events
- **Video Recording**: Capture browser sessions
- **Authentication**: Add API authentication
- **Rate Limiting**: Protect API endpoints

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

---

**Built with**: Chromium, Playwright, Mitmproxy, Flask, Docker

**Maintainer**: [Jack96BO](https://github.com/Jack96BO)
