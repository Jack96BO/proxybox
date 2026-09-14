"""
DNS Manager for ProxyBox
Manages custom DNS routes in-memory for mitmproxy integration
"""

import threading


class DNSManager:
    """Manages custom DNS routes for traffic interception"""
    
    def __init__(self):
        self.routes = {}  # Dictionary: domain -> IP
        self.lock = threading.Lock()
    
    def add_route(self, domain, ip):
        """Add a new DNS route (domain -> IP)"""
        with self.lock:
            # Normalize domain (remove protocol, path, etc.)
            domain = domain.strip().lower()
            
            # Remove http://, https://, trailing slashes
            for prefix in ['http://', 'https://']:
                if domain.startswith(prefix):
                    domain = domain[len(prefix):]
            domain = domain.rstrip('/')
            
            # Validate IP
            ip = ip.strip()
            if not ip:
                return False, "IP address cannot be empty"
            
            # Check if route already exists
            if domain in self.routes:
                return True, f"Route already exists: {domain} -> {self.routes[domain]}"
            
            self.routes[domain] = ip
            return True, f"Route added: {domain} -> {ip}"
    
    def remove_route(self, domain):
        """Remove a DNS route"""
        with self.lock:
            domain = domain.strip().lower()
            for prefix in ['http://', 'https://']:
                if domain.startswith(prefix):
                    domain = domain[len(prefix):]
            domain = domain.rstrip('/')
            
            if domain in self.routes:
                del self.routes[domain]
                return True, f"Route removed: {domain}"
            else:
                return True, f"No route found for {domain}"
    
    def list_routes(self):
        """List all custom DNS routes"""
        with self.lock:
            routes = []
            for domain, ip in self.routes.items():
                routes.append({
                    'domain': domain,
                    'ip': ip,
                    'raw': f"{domain} -> {ip}"
                })
            return routes
    
    def clear_routes(self):
        """Clear all custom DNS routes"""
        with self.lock:
            self.routes.clear()
            return True, "All routes cleared"
    
    def get_route(self, domain):
        """Get the target IP for a domain"""
        with self.lock:
            domain = domain.strip().lower()
            for prefix in ['http://', 'https://']:
                if domain.startswith(prefix):
                    domain = domain[len(prefix):]
            domain = domain.rstrip('/')
            
            return self.routes.get(domain)


# Global DNS manager instance
dns_manager = DNSManager()
