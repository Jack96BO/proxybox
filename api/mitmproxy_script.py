"""
Mitmproxy script for traffic manipulation in API mode
- Supports custom DNS routing via Host header manipulation
- Logs all traffic for debugging
- Can be extended for advanced traffic manipulation
"""

from mitmproxy import http, ctx


# Global DNS routing table (domain -> target IP)
DNS_ROUTES = {}


def request(flow: http.HTTPFlow) -> None:
    """Modify HTTP requests based on DNS routes"""
    try:
        # Check if this request matches any DNS route
        host = flow.request.host
        pretty_url = flow.request.pretty_url
        
        # Extract domain from URL
        domain = host
        
        # Check if domain has a custom route
        if domain in DNS_ROUTES:
            target_ip = DNS_ROUTES[domain]
            ctx.log.info(f"[API] DNS Route: {domain} -> {target_ip}")
            
            # Redirect to target IP
            flow.request.host = target_ip
            
            # Keep the original Host header for SNI and virtual hosting
            flow.request.headers["Host"] = domain
            
            ctx.log.info(f"[API] Redirected request: {pretty_url} -> {target_ip}")
        
        # Log all requests
        ctx.log.info(f"[API] Request: {flow.request.method} {pretty_url}")
        
    except Exception as e:
        ctx.log.error(f"[API] Error in request handler: {e}")


def response(flow: http.HTTPFlow) -> None:
    """Modify HTTP responses"""
    try:
        # Log all responses
        ctx.log.info(f"[API] Response: {flow.response.status_code} {flow.request.pretty_url}")
        
        # Add custom header for API tracking
        flow.response.headers["X-ProxyBox"] = "true"
        
    except Exception as e:
        ctx.log.error(f"[API] Error in response handler: {e}")


def configure(updated: bool) -> None:
    """Configure mitmproxy settings"""
    try:
        if updated:
            return
        
        # Enable SSL interception
        ctx.options.ssl_insecure = True
        ctx.log.info("[API] Mitmproxy configured for SSL interception")
        
    except Exception as e:
        ctx.log.error(f"[API] Error in configure: {e}")


# Functions to manage DNS routes
def add_dns_route(domain, ip):
    """Add a DNS route to the routing table"""
    DNS_ROUTES[domain] = ip
    ctx.log.info(f"[API] Added DNS route: {domain} -> {ip}")


def remove_dns_route(domain):
    """Remove a DNS route from the routing table"""
    if domain in DNS_ROUTES:
        del DNS_ROUTES[domain]
        ctx.log.info(f"[API] Removed DNS route: {domain}")


def list_dns_routes():
    """List all DNS routes"""
    return DNS_ROUTES.copy()


def clear_dns_routes():
    """Clear all DNS routes"""
    DNS_ROUTES.clear()
    ctx.log.info("[API] Cleared all DNS routes")
