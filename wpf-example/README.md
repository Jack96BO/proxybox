# ProxyBox WPF Client

A native WPF application that communicates with the ProxyBox API to control a browser running in Docker. This provides a complete browser automation solution without using WebView2, while still leveraging all ProxyBox functionality (DNS redirection, traffic interception, etc.).

## Features

✅ **Native WPF Application** - No WebView2 dependency  
✅ **Full Browser Control** - Navigate, click, fill forms, execute JavaScript  
✅ **Screenshot Capture** - View screenshots of the remote browser  
✅ **Content Extraction** - Get HTML and text content from pages  
✅ **Multiple Pages** - Manage multiple browser pages simultaneously  
✅ **Connection Status** - Monitor API and browser status  
✅ **Error Handling** - Robust error handling and user feedback  

## Architecture

```
WPF Client (Native) → HTTP/REST → ProxyBox API (Docker) → Playwright + Mitmproxy → Browser
```

The browser runs in Docker with:
- **Playwright** for browser automation
- **Mitmproxy** for traffic interception and manipulation
- **dnsmasq** for DNS redirection (ilmiosito.com → 10.58.54.2)

## Quick Start

### Prerequisites

1. **Start ProxyBox Docker Services**:
   ```bash
   cd proxybox
   docker-compose up -d
   ```

2. **Verify API is Running**:
   ```bash
   curl http://localhost:5000/api/health
   ```

3. **Open WPF Client**:
   - Open the `ProxyBoxClient.sln` in Visual Studio
   - Build and run the application
   - The client will automatically connect to `http://localhost:5000`

### First Run

1. Click **"Test Connection"** to verify the API is accessible
2. Click **"New Page"** to create a browser page
3. Enter a URL (e.g., `http://ilmiosito.com`) and click **"Go"** or press Enter
4. The page will load through the ProxyBox system with:
   - DNS redirection (ilmiosito.com → 10.58.54.2)
   - Traffic interception via Mitmproxy

## Usage Guide

### Navigation
- **New Page**: Create a new browser page
- **Go**: Navigate to the URL in the address bar
- **Back/Forward**: Navigate through browser history
- **Reload**: Refresh the current page

### Content Viewing
- **Screenshot**: Capture and display a screenshot of the current page
- **HTML**: View the HTML source of the current page
- **Text**: View the text content of the current page

### Interaction
- **JavaScript Console**: Write and execute JavaScript on the current page
- **Click**: Click an element using a CSS selector
- **Fill**: Fill a form input using a CSS selector

### Settings
- **API Base URL**: Change the API endpoint (default: `http://localhost:5000`)
- **Test Connection**: Verify the connection to the API

## Project Structure

```
wpf-example/
├── ProxyBoxClient/
│   ├── MainWindow.xaml          # Main UI
│   ├── MainWindow.xaml.cs      # ViewModel and logic
│   ├── App.xaml                 # Application definition
│   ├── App.xaml.cs              # Application code
│   ├── ProxyBoxClient.csproj    # Project file
│   ├── app.manifest             # Application manifest
│   └── App.config               # Configuration
└── README.md                    # This file
```

## Customization

### Change API URL
Edit the `ApiBaseUrl` property in `MainWindow.xaml.cs` or change it in the settings panel at runtime.

### Add New Commands
Add new commands by:
1. Adding a new property for the command
2. Adding a new method for the action
3. Adding a button in the XAML with the command binding

Example:
```csharp
// In MainWindow.xaml.cs
public ICommand NewCommand => new RelayCommand(_ => NewAction());

private async void NewAction()
{
    // Your implementation
}
```

```xml
<!-- In MainWindow.xaml -->
<Button Content="New Action" Command="{Binding NewCommand}" />
```

### Extend Functionality
The API supports many operations. You can extend the client to use:
- `/api/page/{id}/title` - Get page title
- `/api/page/{id}/url` - Get current URL
- `/api/dns/resolve` - Resolve DNS
- And more...

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/browser/start` | Start browser |
| POST | `/api/browser/stop` | Stop browser |
| POST | `/api/page/create` | Create new page |
| POST | `/api/page/{id}/close` | Close page |
| POST | `/api/page/{id}/navigate` | Navigate to URL |
| POST | `/api/page/{id}/screenshot` | Take screenshot |
| GET | `/api/page/{id}/content` | Get HTML content |
| GET | `/api/page/{id}/text` | Get text content |
| POST | `/api/page/{id}/execute` | Execute JavaScript |
| POST | `/api/page/{id}/click` | Click element |
| POST | `/api/page/{id}/fill` | Fill form |
| POST | `/api/page/{id}/back` | Go back |
| POST | `/api/page/{id}/forward` | Go forward |
| POST | `/api/page/{id}/reload` | Reload page |
| GET | `/api/pages/list` | List all pages |

### Request/Response Examples

**Create Page:**
```bash
POST /api/page/create
```
Response:
```json
{
  "status": "ok",
  "page_id": 1
}
```

**Navigate:**
```bash
POST /api/page/1/navigate
Content-Type: application/json

{
  "url": "http://ilmiosito.com"
}
```
Response:
```json
{
  "status": "ok",
  "title": "My Site",
  "url": "http://ilmiosito.com"
}
```

**Screenshot:**
```bash
POST /api/page/1/screenshot
Content-Type: application/json

{
  "format": "png",
  "full_page": true
}
```
Response:
```json
{
  "status": "ok",
  "image": "base64-encoded-image",
  "format": "png"
}
```

## Troubleshooting

### Connection Issues
1. **Verify Docker is running**: `docker ps`
2. **Check API container**: `docker-compose logs api`
3. **Test API directly**: `curl http://localhost:5000/api/health`
4. **Check firewall**: Ensure port 5000 is accessible

### Browser Not Starting
1. **Check browser container**: `docker-compose logs playwright`
2. **Verify dependencies**: Ensure all Docker dependencies are installed
3. **Check resources**: The browser needs sufficient memory and CPU

### Screenshot Not Displaying
1. **Check API response**: Verify the screenshot endpoint returns a valid image
2. **Verify base64 decoding**: The client decodes base64 images
3. **Check image format**: Ensure the format is supported (png, jpeg)

## Advanced Usage

### Custom API Configuration
You can configure the API to use different settings:

**Environment Variables:**
```bash
# In docker-compose.yml
environment:
  - PROXY_SERVER=http://mitmproxy:8080
  - DNS_SERVER=172.20.0.2
```

**Custom DNS Redirection:**
Edit `docker/dnsmasq/config/dnsmasq.conf`:
```conf
address=/custom-domain.com/10.58.54.2
```

**Custom Traffic Rules:**
Edit `api/mitmproxy_script.py`:
```python
def request(flow: http.HTTPFlow):
    if "block-me.com" in flow.request.pretty_url:
        flow.response = http.Response.make(403)
```

## Deployment

### Deploy API to Production
1. **Docker**: Use the provided Docker configuration
2. **Kubernetes**: Create a deployment and service
3. **Cloud**: Deploy to Azure, AWS, or other cloud providers

### Update API URL in Client
After deployment, update the `ApiBaseUrl` in the WPF client to point to your production API.

## Security Considerations

1. **HTTPS**: Use HTTPS for production deployments
2. **Authentication**: Add authentication to the API
3. **Rate Limiting**: Implement rate limiting for public APIs
4. **CORS**: Configure CORS properly for web clients

## Performance Optimization

1. **Browser Pool**: Maintain a pool of browser instances
2. **Page Caching**: Cache frequently accessed pages
3. **Connection Reuse**: Reuse HTTP connections
4. **Async Operations**: Use async/await for all operations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the [MIT License](../../LICENSE).

## Support

For issues or questions:
- Open an issue on GitHub
- Check the documentation
- Review the API reference

## Acknowledgments

- [Playwright](https://playwright.dev/) - Browser automation
- [Mitmproxy](https://mitmproxy.org/) - Traffic interception
- [dnsmasq](http://www.thekelleys.org.uk/dnsmasq/doc.html) - DNS forwarding
- [Docker](https://www.docker.com/) - Container platform
- [Flask](https://flask.palletsprojects.com/) - Web framework

---

**Project**: [ProxyBox](https://github.com/Jack96BO/proxybox)  
**Maintainer**: Jack96BO  
**Status**: Active Development
