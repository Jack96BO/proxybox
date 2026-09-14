"""
Mitmproxy script for traffic manipulation in API mode
- Redirects ilmiosito.com to 10.58.54.2
- Logs all traffic for debugging
- Can be extended for advanced traffic manipulation
"""

from mitmproxy import http, ctx


def request(flow: http.HTTPFlow) -> None:
    """Modify HTTP requests"""
    # Redirect ilmiosito.com to 10.58.54.2
    if "ilmiosito.com" in flow.request.pretty_url:
        ctx.log.info(f"[API] Intercepted request to: {flow.request.pretty_url}")
        
        # Change the host to the target IP
        flow.request.host = "10.58.54.2"
        
        # Keep the original Host header for SNI
        flow.request.headers["Host"] = "ilmiosito.com"
        
        ctx.log.info(f"[API] Redirected to: {flow.request.host}")
    
    # Log all requests
    ctx.log.info(f"[API] Request: {flow.request.method} {flow.request.pretty_url}")


def response(flow: http.HTTPFlow) -> None:
    """Modify HTTP responses"""
    # Log all responses
    ctx.log.info(f"[API] Response: {flow.response.status_code} {flow.request.pretty_url}")
    
    # Modify responses from the target IP
    if flow.request.host == "10.58.54.2" or "ilmiosito.com" in flow.request.pretty_url:
        ctx.log.info(f"[API] Modifying response from: {flow.request.pretty_url}")
        
        # Add custom header for API tracking
        flow.response.headers["X-ProxyBox"] = "true"


def configure(updated: bool) -> None:
    """Configure mitmproxy settings"""
    if updated:
        return
    
    # Enable SSL interception
    ctx.options.ssl_insecure = True
    ctx.log.info("[API] Mitmproxy configured for SSL interception")
