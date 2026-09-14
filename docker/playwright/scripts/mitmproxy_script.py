"""
Mitmproxy script for traffic manipulation
- Redirects ilmiosito.com to 10.58.54.2
- Modifies HTTP requests and responses
- Can be extended for DNS spoofing and other manipulations
"""

from mitmproxy import http, ctx


def request(flow: http.HTTPFlow) -> None:
    """Modify HTTP requests"""
    # Redirect ilmiosito.com to 10.58.54.2
    if "ilmiosito.com" in flow.request.pretty_url:
        ctx.log.info(f"Intercepted request to: {flow.request.pretty_url}")
        
        # Change the host to the target IP
        flow.request.host = "10.58.54.2"
        
        # Keep the original Host header for SNI
        flow.request.headers["Host"] = "ilmiosito.com"
        
        ctx.log.info(f"Redirected to: {flow.request.host}")
    
    # Example: Modify headers
    # flow.request.headers["User-Agent"] = "CustomUserAgent"
    
    # Example: Block specific requests
    # if "block-me.com" in flow.request.pretty_url:
    #     flow.response = http.Response.make(403)


def response(flow: http.HTTPFlow) -> None:
    """Modify HTTP responses"""
    # Modify responses from the target IP
    if flow.request.host == "10.58.54.2" or "ilmiosito.com" in flow.request.pretty_url:
        ctx.log.info(f"Modifying response from: {flow.request.pretty_url}")
        
        # Example: Inject custom content
        # if flow.response and flow.response.content:
        #     original_content = flow.response.content
        #     modified_content = b"<h1>Modified Response</h1>" + original_content
        #     flow.response.content = modified_content
        #     flow.response.headers["Content-Length"] = str(len(modified_content))
    
    # Example: Log all responses
    # ctx.log.info(f"Response: {flow.response.status_code} {flow.request.pretty_url}")


def configure(updated: bool) -> None:
    """Configure mitmproxy settings"""
    if updated:
        return
    
    # Enable SSL interception
    ctx.options.ssl_insecure = True
    ctx.log.info("Mitmproxy configured for SSL interception")


def tls_handshake(data: http.TLSHandshakeData) -> None:
    """Handle TLS handshake for SNI-based routing"""
    ctx.log.info(f"TLS handshake with: {data.server_hostname}")
