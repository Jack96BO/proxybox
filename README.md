# ProxyBox - Browser Automation & Traffic Interception

ProxyBox is a complete solution for browser automation, traffic interception, and DNS routing in a Docker container. It combines Playwright for browser automation with Mitmproxy for traffic manipulation, providing a powerful API and web dashboard.

## Features

- **Browser Automation**: Full control over Chromium browser via Playwright
- **Traffic Interception**: Modify HTTP/HTTPS requests and responses with Mitmproxy
- **DNS Routing**: Custom DNS routes to redirect domains to specific IPs
- **Web Dashboard**: Interactive HTML dashboard for easy control
- **REST API**: Complete API for programmatic control
- **Docker Ready**: Optimized for deployment on Render.com and other platforms

## Architecture

```
+------------------+
|   Web Dashboard  |  (HTML/JS)
+------------------+
         |
         v
+------------------+
|    Flask API     |  (Python)
+------------------+
         |
    +----+----+
    |         |
+---v---+ +--v--+
|Playwright|Mitmproxy|
+---+---+ +--+--+
    |         |
    v         v
+------------------+
|   Chromium Browser with Proxy |
+------------------+
```

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Jack96BO/proxybox.git
cd proxybox
```

### 2. Run with Docker Compose (Development)

```bash
docker-compose up -d
```

This starts:
- Flask API on port 5000
- Mitmproxy on port 8080
- dnsmasq on port 53 (optional)

### 3. Deploy to Render.com

1. Create a new Web Service on Render
2. Select "Docker" as the runtime
3. Use `Dockerfile.render` as the Dockerfile path
4. Set environment variables (see below)
5. Deploy!

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROXY_SERVER` | Proxy server URL for Playwright | `http://localhost:8080` |
| `DNS_SERVER` | DNS server IP | `127.0.0.1` |
| `FLASK_HOST` | Flask server host | `0.0.0.0` |
| `FLASK_PORT` | Flask server port | `5000` |
| `MITMPROXY_PORT` | Mitmproxy port | `8080` |
| `DNSMASQ_PORT` | Dnsmasq port | `53` |

## API Endpoints

### Browser Control

- `POST /api/browser/start` - Start browser
- `POST /api/browser/stop` - Stop browser
- `GET /api/health` - Health check

### Page Management

- `POST /api/page/create` - Create new page
- `POST /api/page/<id>/close` - Close page
- `POST /api/page/<id>/navigate` - Navigate to URL
- `POST /api/page/<id>/screenshot` - Take screenshot
- `GET /api/page/<id>/content` - Get HTML content
- `GET /api/page/<id>/text` - Get text content
- `POST /api/page/<id>/execute` - Execute JavaScript
- `POST /api/page/<id>/click` - Click element
- `POST /api/page/<id>/fill` - Fill form
- `GET /api/pages/list` - List all pages

### DNS Routing

- `GET /api/dns/routes` - List all DNS routes
- `POST /api/dns/routes` - Add new DNS route
- `DELETE /api/dns/routes/<domain>` - Remove DNS route
- `DELETE /api/dns/routes` - Clear all DNS routes

### Element Interaction

- `POST /api/page/<id>/reload` - Reload page
- `POST /api/page/<id>/back` - Go back
- `POST /api/page/<id>/forward` - Go forward
- `GET /api/page/<id>/title` - Get page title
- `GET /api/page/<id>/url` - Get current URL

## Web Dashboard

Access the dashboard at `http://localhost:5000` (or your deployed URL)

### Features:

- **Browser View**: Embedded browser view via iframe
- **Screenshot**: Capture screenshots of pages
- **HTML/Text View**: View page content
- **JavaScript Execution**: Run custom scripts on pages
- **Element Interaction**: Click and fill form elements
- **DNS Management**: Add/remove DNS routes
- **Status Monitoring**: Real-time status of all components

## Usage Examples

### Create a Page and Navigate

```bash
# Create a new page
curl -X POST http://localhost:5000/api/page/create

# Navigate to URL (replace <page_id>)
curl -X POST http://localhost:5000/api/page/<page_id>/navigate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://google.com"}'
```

### Add DNS Route

```bash
# Add a DNS route
curl -X POST http://localhost:5000/api/dns/routes \
  -H "Content-Type: application/json" \
  -d '{"domain": "example.com", "ip": "10.58.54.2"}'

# List all routes
curl http://localhost:5000/api/dns/routes
```

### Take Screenshot

```bash
# Take screenshot (returns base64 encoded image)
curl -X POST http://localhost:5000/api/page/<page_id>/screenshot \
  -H "Content-Type: application/json" \
  -d '{"format": "png", "full_page": true}'
```

## Integration with WPF (WebView2)

To integrate ProxyBox with a WPF application using WebView2:

### Option 1: Use as External Service

```csharp
// Configure WebView2 to use ProxyBox as proxy
var options = new CoreWebView2EnvironmentOptions
{
    AdditionalBrowserArguments = $"--proxy-server=http://localhost:8080 --ignore-certificate-errors"
};

var env = await CoreWebView2Environment.CreateAsync(null, null, options);
await webView.EnsureCoreWebView2Async(env);
```

### Option 2: Embed Dashboard

```csharp
// Navigate to ProxyBox dashboard
webView.CoreWebView2.Navigate("http://localhost:5000");
```

### Option 3: Direct API Calls

```csharp
using (var client = new HttpClient())
{
    // Add DNS route
    var response = await client.PostAsync(
        "http://localhost:5000/api/dns/routes",
        new StringContent(
            JsonConvert.SerializeObject(new { domain = "example.com", ip = "10.58.54.2" }),
            Encoding.UTF8,
            "application/json"
        )
    );
}
```

## Custom DNS Routing

ProxyBox supports custom DNS routing without requiring dnsmasq. Routes are managed in-memory and applied to Mitmproxy:

1. Add a route via API: `POST /api/dns/routes` with `{domain: "example.com", ip: "10.58.54.2"}`
2. The route is automatically applied to Mitmproxy
3. All requests to `example.com` will be redirected to `10.58.54.2`
4. The original Host header is preserved for SNI

## Deployment to Render.com

1. Create a new Web Service
2. Select "Docker" as the runtime
3. Configure:
   - **Dockerfile Path**: `Dockerfile.render`
   - **Build Command**: (leave empty)
   - **Start Command**: (leave empty - uses CMD from Dockerfile)
4. Set environment variables:
   - `PROXY_SERVER`: `http://localhost:8080`
   - `MITMPROXY_PORT`: `8080`
   - `FLASK_PORT`: `5000`
5. Deploy!

## Troubleshooting

### Mitmproxy Console Error

If you see `mitmproxy's console interface requires a tty`, use `mitmdump` instead:

```bash
mitmdump -s mitmproxy_script.py --listen-port 8080
```

### Browser Not Starting

Ensure all dependencies are installed:
```bash
playwright install chromium --with-deps
```

### Template Not Found Error

Make sure the templates folder exists and contains `index.html`:
```bash
mkdir -p api/templates
cp api/templates/index.html api/templates/
```

## Project Structure

```
proxybox/
├── api/
│   ├── app.py              # Flask API backend
│   ├── mitmproxy_script.py # Mitmproxy traffic handler
│   ├── dns_manager.py      # DNS route manager
│   └── templates/
│       └── index.html      # Web dashboard
├── docker/
│   ├── dnsmasq/            # dnsmasq Docker configuration
│   └── playwright/          # Playwright Docker configuration
├── Dockerfile.render       # Render.com Dockerfile
├── docker-compose.yml      # Docker Compose configuration
└── README.md               # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - feel free to use, modify, and distribute.

## Support

For issues or questions, please open a GitHub issue.

---

**ProxyBox** - Powerful browser automation and traffic interception in a box!
