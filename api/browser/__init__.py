"""
Browser Module for ProxyBox
Chromium Standalone + CDP Architecture
"""

from .manager import BrowserManager
from .chromium import ChromiumProcess

__all__ = ['BrowserManager', 'ChromiumProcess']
