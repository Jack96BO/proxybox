"""
DNS Manager for ProxyBox
Manages custom DNS routes and integrates with Mitmproxy
"""

import threading
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DNSManager:
    """
    Manages custom DNS routes for traffic routing
    Routes are stored in-memory and applied to Mitmproxy
    """
    
    def __init__(self):
        self.routes: Dict[str, str] = {}  # domain -> IP
        self.lock = threading.Lock()
        self.mitmproxy_addon = None
    
    def add_route(self, domain: str, ip: str) -> Tuple[bool, str]:
        """Add a new DNS route"""
        with self.lock:
            # Normalize domain
            domain = self._normalize_domain(domain)
            ip = ip.strip()
            
            if not domain or not ip:
                return False, "Domain and IP are required"
            
            if domain in self.routes:
                return True, f"Route already exists: {domain} -> {self.routes[domain]}"
            
            self.routes[domain] = ip
            logger.info(f"Added DNS route: {domain} -> {ip}")
            
            # Apply to Mitmproxy if available
            if self.mitmproxy_addon:
                try:
                    self.mitmproxy_addon.add_route(domain, ip)
                except Exception as e:
                    logger.warning(f"Failed to apply route to Mitmproxy: {e}")
            
            return True, f"Route added: {domain} -> {ip}"
    
    def remove_route(self, domain: str) -> Tuple[bool, str]:
        """Remove a DNS route"""
        with self.lock:
            domain = self._normalize_domain(domain)
            
            if domain not in self.routes:
                return True, f"No route found for {domain}"
            
            ip = self.routes[domain]
            del self.routes[domain]
            logger.info(f"Removed DNS route: {domain} -> {ip}")
            
            # Apply to Mitmproxy if available
            if self.mitmproxy_addon:
                try:
                    self.mitmproxy_addon.remove_route(domain)
                except Exception as e:
                    logger.warning(f"Failed to remove route from Mitmproxy: {e}")
            
            return True, f"Route removed: {domain}"
    
    def list_routes(self) -> List[Dict[str, str]]:
        """List all DNS routes"""
        with self.lock:
            return [
                {"domain": domain, "ip": ip, "raw": f"{domain} -> {ip}"}
                for domain, ip in self.routes.items()
            ]
    
    def clear_routes(self) -> Tuple[bool, str]:
        """Clear all DNS routes"""
        with self.lock:
            self.routes.clear()
            logger.info("Cleared all DNS routes")
            
            # Apply to Mitmproxy if available
            if self.mitmproxy_addon:
                try:
                    self.mitmproxy_addon.clear_routes()
                except Exception as e:
                    logger.warning(f"Failed to clear routes from Mitmproxy: {e}")
            
            return True, "All routes cleared"
    
    def get_route(self, domain: str) -> Optional[str]:
        """Get the target IP for a domain"""
        with self.lock:
            domain = self._normalize_domain(domain)
            return self.routes.get(domain)
    
    def _normalize_domain(self, domain: str) -> str:
        """Normalize domain by removing protocol and path"""
        domain = domain.strip().lower()
        for prefix in ['http://', 'https://']:
            if domain.startswith(prefix):
                domain = domain[len(prefix):]
        return domain.rstrip('/')
    
    def set_mitmproxy_addon(self, addon):
        """Set reference to Mitmproxy addon for direct updates"""
        self.mitmproxy_addon = addon
        logger.info("DNSManager connected to Mitmproxy addon")
