# ProxyBox - Docker-based Browser Proxy System

A complete open-source solution for running a browser inside Docker with traffic manipulation capabilities, similar to BrowserBox. This project allows you to:

- Run a real browser (Chromium via Playwright) inside Docker
- Intercept and modify HTTP/HTTPS traffic using Mitmproxy
- Redirect DNS requests (e.g., ilmiosito.com → 10.58.54.2) using dnsmasq
- Perform web scraping and automation
- Integrate with WPF applications via WebView2 with proxy configuration

## Features

✅ **Browser Automation**: Full Chromium browser control via Playwright  
✅ **Traffic Interception**: HTTP/HTTPS traffic modification with Mitmproxy  
✅ **DNS Redirection**: Custom DNS resolution with dnsmasq  
✅ **Docker Integration**: Complete containerized solution  
✅ **Scraping Capabilities**: Extract data from web pages  
✅ **Proxy Integration**: Works with any proxy-aware application  
✅ **Open Source**: Fully customizable and extensible  

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Host Machine                            │
├─────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │  dnsmasq         │    │  Playwright      │                 │
│  │  (DNS Server)    │    │  + Mitmproxy    │                 │
│  │                  │    │                 │                 │
│  │  Port: 53/udp    │◄──►│  Port: 8080     │                 │
│  │  (mapped to      │    │  (HTTP Proxy)   │                 │
│  │   5353/udp)     │    │                 │                 │
│  └─────────────────┘    └─────────────────┘                 │
│           ▲                                                  │
│           │                                                  │
│  ┌────────┴────────┐                                       │
│  │  Custom Network  │  172.20.0.0/24                       │
│  │  (proxy_network) │                                       │
│  └─────────────────┘                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker (v20.10+ recommended)
- Docker Compose (v2.0+)
- Git

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Jack96BO/proxybox.git
   cd proxybox
   ```

2. **Build and start the containers**:
   ```bash
   docker-compose up --build
   ```

3. **Access the services**:
   - **Mitmproxy Web Interface**: http://localhost:8080
   - **DNS Server**: UDP port 5353 on localhost

### Usage Examples

#### Example 1: DNS Redirection

The system automatically redirects `ilmiosito.com` to `10.58.54.2` via dnsmasq. To test:

```bash
# Query the DNS server directly
dig @localhost -p 5353 ilmiosito.com

# Should return: 10.58.54.2
```

#### Example 2: Browser Automation with Traffic Interception

The Playwright container will:
1. Use dnsmasq for DNS resolution
2. Route all traffic through Mitmproxy
3. Automatically redirect ilmiosito.com to 10.58.54.2
4. Allow traffic modification via Mitmproxy scripts

#### Example 3: Standalone Mitmproxy

For advanced traffic manipulation, use the standalone Mitmproxy container:

```bash
# Start only mitmproxy
docker-compose up mitmproxy

# Access web interface at http://localhost:8081
```

### Configuration

#### DNS Redirection (dnsmasq)

Edit `docker/dnsmasq/config/dnsmasq.conf` to add more DNS redirections:

```conf
# Redirect multiple domains
address=/domain1.com/10.58.54.2
address=/domain2.com/10.58.54.3
address=/domain3.com/192.168.1.100

# Upstream DNS servers
server=8.8.8.8
server=8.8.4.4
```

#### Traffic Manipulation (Mitmproxy)

Edit `docker/playwright/scripts/mitmproxy_script.py` to customize traffic handling:

```python
# Redirect specific domains
def request(flow: http.HTTPFlow) -> None:
    if "example.com" in flow.request.pretty_url:
        flow.request.host = "10.58.54.2"
        flow.request.headers["Host"] = "example.com"
    
    # Modify headers
    if "block-ads.com" in flow.request.pretty_url:
        flow.response = http.Response.make(403)

# Modify responses
def response(flow: http.HTTPFlow) -> None:
    if flow.request.host == "10.58.54.2":
        # Inject custom content
        flow.response.content = b"<h1>Modified!</h1>"
```

#### Browser Automation (Playwright)

Edit `docker/playwright/scripts/playwright_script.py` for custom automation:

```python
# Custom navigation and scraping
page.goto("http://ilmiosito.com")

# Extract data
title = page.title()
links = page.query_selector_all("a")

# Take screenshots
page.screenshot(path="/app/screenshot.png")

# Modify page content
page.evaluate("""
    document.body.innerHTML = '<h1>Custom Content</h1>';
""")
```

### Integration with WPF (WebView2)

To integrate with a WPF application using WebView2:

```csharp
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

// Configure WebView2 to use the proxy
var options = new CoreWebView2EnvironmentOptions
{
    AdditionalBrowserArguments = "--proxy-server=http://localhost:8080"
};

var env = CoreWebView2Environment.CreateAsync(null, null, options).Result;
webView.EnsureCoreWebView2Async(env).Wait();
webView.CoreWebView2.Navigate("http://ilmiosito.com");
```

### Custom DNS Resolution on Host

To use the dnsmasq server on your host machine:

**Linux/macOS**:
```bash
# Add to /etc/resolv.conf (temporarily)
echo "nameserver 127.0.0.1" | sudo tee -a /etc/resolv.conf

# Or use port 5353
echo "nameserver 127.0.0.1#5353" | sudo tee -a /etc/resolv.conf
```

**Windows**:
1. Go to Network Settings
2. Add a custom DNS server: `127.0.0.1`
3. For port 5353, use a tool like Simple DNS Plus or modify the configuration

## Docker Commands

### Start all services:
```bash
docker-compose up -d
```

### Stop all services:
```bash
docker-compose down
```

### View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f playwright
```

### Rebuild containers:
```bash
docker-compose up --build -d
```

### Access containers:
```bash
# Access playwright container
docker exec -it playwright-browser sh

# Access dnsmasq container
docker exec -it dnsmasq-proxy sh
```

## Project Structure

```
proxybox/
├── docker/
│   ├── dnsmasq/
│   │   ├── Dockerfile
│   │   └── config/
│   │       └── dnsmasq.conf
│   └── playwright/
│       ├── Dockerfile
│       └── scripts/
│           ├── mitmproxy_script.py
│           └── playwright_script.py
├── docker-compose.yml
├── README.md
└── .gitignore
```

## Customization

### Add More DNS Redirections

Edit `docker/dnsmasq/config/dnsmasq.conf`:
```conf
address=/domain1.com/10.58.54.2
address=/domain2.com/192.168.1.100
address=/*.example.com/10.0.0.1
```

### Add More Traffic Rules

Edit `docker/playwright/scripts/mitmproxy_script.py`:
```python
def request(flow: http.HTTPFlow) -> None:
    # Redirect specific domains
    if "block-me.com" in flow.request.pretty_url:
        flow.response = http.Response.make(403)
    
    # Modify headers
    if "modify-headers.com" in flow.request.pretty_url:
        flow.request.headers["User-Agent"] = "CustomAgent"
        flow.request.headers["X-Custom-Header"] = "CustomValue"
    
    # Redirect to different IP
    if "redirect-me.com" in flow.request.pretty_url:
        flow.request.host = "192.168.1.100"
```

### Add More Browser Automation

Edit `docker/playwright/scripts/playwright_script.py`:
```python
# Multiple pages
page1 = browser.new_page()
page2 = browser.new_page()

# Parallel navigation
page1.goto("http://site1.com")
page2.goto("http://site2.com")

# Form submission
page.fill("#username", "testuser")
page.fill("#password", "testpass")
page.click("#submit")

# Download files
page.goto("http://example.com/file.zip")
page.wait_for_download()
```

## Troubleshooting

### DNS Not Working

1. Check if dnsmasq is running:
   ```bash
   docker-compose logs dnsmasq
   ```

2. Test DNS resolution:
   ```bash
   dig @localhost -p 5353 ilmiosito.com
   ```

3. Check if the container is using the correct DNS:
   ```bash
   docker exec -it playwright-browser cat /etc/resolv.conf
   ```

### Proxy Not Working

1. Check if mitmproxy is running:
   ```bash
   docker-compose logs playwright
   ```

2. Test proxy connectivity:
   ```bash
   curl -x http://localhost:8080 http://example.com
   ```

3. Check mitmproxy logs for errors

### Browser Not Starting

1. Check playwright logs:
   ```bash
   docker-compose logs playwright
   ```

2. Ensure all dependencies are installed:
   ```bash
   docker exec -it playwright-browser playwright install
   ```

3. Try running in headless mode (edit playwright_script.py)

## Security Considerations

1. **SSL Certificates**: Mitmproxy generates its own SSL certificates. For production use, consider:
   - Using your own CA certificates
   - Configuring browsers to trust the proxy's CA

2. **Network Isolation**: The containers are on a custom network. For production:
   - Consider using a more restrictive network configuration
   - Use firewall rules to limit access

3. **Authentication**: For public-facing proxies:
   - Add authentication to mitmproxy
   - Use HTTPS for the web interface

## Performance Optimization

1. **Reduce Image Size**:
   - Use multi-stage builds
   - Remove unnecessary dependencies
   - Use alpine-based images where possible

2. **Caching**:
   - Enable Docker build cache
   - Use .dockerignore to exclude unnecessary files

3. **Resource Limits**:
   - Set CPU and memory limits in docker-compose.yml
   - Use `--memory` and `--cpus` flags

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## Acknowledgments

- [Playwright](https://playwright.dev/) - Browser automation framework
- [Mitmproxy](https://mitmproxy.org/) - Interactive man-in-the-middle proxy
- [dnsmasq](http://www.thekelleys.org.uk/dnsmasq/doc.html) - Lightweight DNS forwarder
- [Docker](https://www.docker.com/) - Container platform

---

**Project Maintainer**: Jack96BO  
**GitHub**: [Jack96BO/proxybox](https://github.com/Jack96BO/proxybox)  
**Status**: Active Development
