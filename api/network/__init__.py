"""
Network Module for ProxyBox
DNS and Proxy Management
"""

from .dns_manager import DNSManager
from .proxy_manager import ProxyManager

__all__ = ['DNSManager', 'ProxyManager']
