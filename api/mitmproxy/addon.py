"""
Mitmproxy Addon for ProxyBox
Handles traffic interception, DNS routing, and request/response modification
"""

from mitmproxy import http, ctx
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class MitmproxyAddon:
    """
    Mitmproxy addon that integrates with ProxyBox
    - Intercepts HTTP/HTTPS traffic
    - Applies DNS routing
    - Modifies requests/responses
    - Logs traffic for debugging
    """
    
    def __init__(self):
        self.dns_routes: Dict[str, str] = {}  # domain -> IP
        self.request_count = 0
        self.response_count = 0
    
    def request(self, flow: http.HTTPFlow) -> None:
        """Handle HTTP requests"""
        try:
            self.request_count += 1
            
            # Extract domain
            host = flow.request.host
            pretty_url = flow.request.pretty_url
            
            # Apply DNS routing
            if host in self.dns_routes:
                target_ip = self.dns_routes[host]
                logger.info(f"[MITMPROXY] DNS Route: {host} -> {target_ip}")
                
                # Redirect to target IP
                original_host = host
                flow.request.host = target_ip
                
                # Preserve original Host header for SNI
                flow.request.headers["Host"] = original_host
                
                logger.info(f"[MITMPROXY] Redirected: {pretty_url} -> {target_ip}")
            
            # Log request
            logger.info(f"[MITMPROXY] Request #{self.request_count}: {flow.request.method} {pretty_url}")
            
            # Add custom headers for tracking
            flow.request.headers["X-ProxyBox"] = "true"
            
        except Exception as e:
            logger.error(f"[MITMPROXY] Error in request handler: {e}")
    
    def response(self, flow: http.HTTPFlow) -> None:
        """Handle HTTP responses"""
        try:
            self.response_count += 1
            
            # Log response
            logger.info(f"[MITMPROXY] Response #{self.response_count}: {flow.response.status_code} {flow.request.pretty_url}")
            
            # Add custom headers
            flow.response.headers["X-ProxyBox"] = "true"
            flow.response.headers["X-ProxyBox-Request-ID"] = str(self.request_count)
            
        except Exception as e:
            logger.error(f"[MITMPROXY] Error in response handler: {e}")
    
    def configure(self, updated: bool) -> None:
        """Configure Mitmproxy"""
        if updated:
            return
        
        # Enable SSL interception
        ctx.options.ssl_insecure = True
        logger.info("[MITMPROXY] SSL interception enabled")
    
    # DNS Management Methods
    def add_route(self, domain: str, ip: str) -> None:
        """Add a DNS route"""
        domain = self._normalize_domain(domain)
        self.dns_routes[domain] = ip
        logger.info(f"[MITMPROXY] Added DNS route: {domain} -> {ip}")
    
    def remove_route(self, domain: str) -> None:
        """Remove a DNS route"""
        domain = self._normalize_domain(domain)
        if domain in self.dns_routes:
            del self.dns_routes[domain]
            logger.info(f"[MITMPROXY] Removed DNS route: {domain}")
    
    def clear_routes(self) -> None:
        """Clear all DNS routes"""
        self.dns_routes.clear()
        logger.info("[MITMPROXY] Cleared all DNS routes")
    
    def list_routes(self) -> Dict[str, str]:
        """List all DNS routes"""
        return self.dns_routes.copy()
    
    def get_route(self, domain: str) -> Optional[str]:
        """Get target IP for a domain"""
        domain = self._normalize_domain(domain)
        return self.dns_routes.get(domain)
    
    def _normalize_domain(self, domain: str) -> str:
        """Normalize domain"""
        domain = domain.strip().lower()
        for prefix in ['http://', 'https://']:
            if domain.startswith(prefix):
                domain = domain[len(prefix):]
        return domain.rstrip('/')
    
    # Statistics
    def get_stats(self) -> Dict[str, int]:
        """Get traffic statistics"""
        return {
            "requests": self.request_count,
            "responses": self.response_count,
            "dns_routes": len(self.dns_routes)
        }
    
    def reset_stats(self) -> None:
        """Reset traffic statistics"""
        self.request_count = 0
        self.response_count = 0


# Create global addon instance
addon = MitmproxyAddon()
