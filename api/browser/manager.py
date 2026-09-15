"""
Browser Manager for ProxyBox
Manages Chromium standalone via CDP
"""

import asyncio
import logging
import os
from typing import Optional, Dict, List, Any
from playwright.async_api import async_playwright

from .chromium import ChromiumProcess

logger = logging.getLogger(__name__)


class BrowserManager:
    """
    Manages browser sessions via CDP
    Handles connection, page creation, and session management
    """
    
    def __init__(
        self,
        cdp_port: int = 9222,
        proxy_server: Optional[str] = None,
        user_data_dir: str = "/data/chromium"
    ):
        self.cdp_port = cdp_port
        self.proxy_server = proxy_server
        self.user_data_dir = user_data_dir
        
        self.chromium_process = ChromiumProcess(
            cdp_port=cdp_port,
            proxy_server=proxy_server,
            user_data_dir=user_data_dir
        )
        
        self.playwright = None
        self.browser = None
        self.contexts: Dict[str, Any] = {}
        self.pages: Dict[str, Dict[str, Any]] = {}
        self.next_page_id = 1
        self.next_context_id = 1
        
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize BrowserManager"""
        if self._initialized:
            return True
        
        try:
            # Start Chromium process
            if not self.chromium_process.start():
                logger.error("Failed to start Chromium process")
                return False
            
            # Initialize Playwright
            self.playwright = await async_playwright().start()
            
            # Connect to Chromium via CDP
            cdp_url = self.chromium_process.get_cdp_url()
            if not cdp_url:
                logger.error("CDP URL not available")
                return False
            
            logger.info(f"Connecting to Chromium via CDP at {cdp_url}")
            self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
            
            # Create default context
            default_context = await self.browser.new_context()
            self.contexts["default"] = {
                "id": "default",
                "context": default_context
            }
            
            self._initialized = True
            logger.info("BrowserManager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing BrowserManager: {e}")
            await self.cleanup()
            return False
    
    async def cleanup(self) -> None:
        """Cleanup all resources"""
        try:
            if self.browser:
                await self.browser.close()
                self.browser = None
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
        
        try:
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
        except Exception as e:
            logger.error(f"Error stopping playwright: {e}")
        
        try:
            if self.chromium_process:
                self.chromium_process.stop()
        except Exception as e:
            logger.error(f"Error stopping chromium process: {e}")
        
        self.contexts.clear()
        self.pages.clear()
        self._initialized = False
    
    async def start(self) -> bool:
        """Start the browser"""
        return await self.initialize()
    
    async def stop(self) -> bool:
        """Stop the browser"""
        await self.cleanup()
        return True
    
    async def restart(self) -> bool:
        """Restart the browser"""
        await self.stop()
        return await self.start()
    
    async def connect(self) -> bool:
        """Connect to existing Chromium instance"""
        if self._initialized:
            return True
        return await self.initialize()
    
    async def create_context(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Create a new browser context"""
        if not self._initialized:
            await self.initialize()
        
        try:
            context_name = name or f"context_{self.next_context_id}"
            self.next_context_id += 1
            
            context = await self.browser.new_context()
            context_id = context_name
            
            self.contexts[context_id] = {
                "id": context_id,
                "name": context_name,
                "context": context
            }
            
            logger.info(f"Created new context: {context_id}")
            return {"status": "ok", "context_id": context_id}
            
        except Exception as e:
            logger.error(f"Error creating context: {e}")
            return {"status": "error", "error": str(e)}
    
    async def create_page(
        self,
        context_id: Optional[str] = None,
        url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new page"""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Use default context if not specified
            ctx_id = context_id or "default"
            if ctx_id not in self.contexts:
                # Create context if it doesn't exist
                await self.create_context(ctx_id)
            
            context = self.contexts[ctx_id]["context"]
            page = await context.new_page()
            
            page_id = str(self.next_page_id)
            self.next_page_id += 1
            
            # Navigate to URL if provided
            if url:
                await page.goto(url, timeout=30000)
            
            self.pages[page_id] = {
                "id": page_id,
                "context_id": ctx_id,
                "page": page,
                "url": url or "about:blank",
                "title": await page.title()
            }
            
            logger.info(f"Created new page: {page_id}")
            return {
                "status": "ok",
                "page_id": page_id,
                "context_id": ctx_id,
                "url": url or "about:blank"
            }
            
        except Exception as e:
            logger.error(f"Error creating page: {e}")
            return {"status": "error", "error": str(e)}
    
    async def close_page(self, page_id: str) -> Dict[str, Any]:
        """Close a page"""
        if page_id not in self.pages:
            return {"status": "error", "error": "Page not found"}
        
        try:
            page = self.pages[page_id]["page"]
            await page.close()
            del self.pages[page_id]
            logger.info(f"Closed page: {page_id}")
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"Error closing page: {e}")
            return {"status": "error", "error": str(e)}
    
    async def list_pages(self) -> Dict[str, Any]:
        """List all pages"""
        pages_info = []
        for page_id, page_data in self.pages.items():
            try:
                pages_info.append({
                    "page_id": page_id,
                    "context_id": page_data["context_id"],
                    "url": page_data["url"],
                    "title": await page_data["page"].title()
                })
            except:
                pass
        
        return {
            "status": "ok",
            "pages": pages_info,
            "count": len(pages_info)
        }
    
    async def navigate(
        self,
        page_id: str,
        url: str,
        wait_until: str = "domcontentloaded"
    ) -> Dict[str, Any]:
        """Navigate to a URL"""
        if page_id not in self.pages:
            return {"status": "error", "error": "Page not found"}
        
        try:
            page = self.pages[page_id]["page"]
            await page.goto(url, timeout=30000, wait_until=wait_until)
            
            self.pages[page_id]["url"] = url
            self.pages[page_id]["title"] = await page.title()
            
            logger.info(f"Navigated page {page_id} to {url}")
            return {
                "status": "ok",
                "page_id": page_id,
                "url": url,
                "title": await page.title()
            }
        except Exception as e:
            logger.error(f"Error navigating: {e}")
            return {"status": "error", "error": str(e)}
    
    async def screenshot(
        self,
        page_id: str,
        full_page: bool = False,
        format: str = "png"
    ) -> Dict[str, Any]:
        """Take a screenshot"""
        if page_id not in self.pages:
            return {"status": "error", "error": "Page not found"}
        
        try:
            page = self.pages[page_id]["page"]
            screenshot_bytes = await page.screenshot(
                full_page=full_page,
                type=format
            )
            
            import base64
            encoded = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            logger.info(f"Took screenshot of page {page_id}")
            return {
                "status": "ok",
                "image": encoded,
                "format": format
            }
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return {"status": "error", "error": str(e)}
    
    async def execute_script(
        self,
        page_id: str,
        script: str
    ) -> Dict[str, Any]:
        """Execute JavaScript on a page"""
        if page_id not in self.pages:
            return {"status": "error", "error": "Page not found"}
        
        try:
            page = self.pages[page_id]["page"]
            result = await page.evaluate(script)
            
            logger.info(f"Executed script on page {page_id}")
            return {
                "status": "ok",
                "result": result
            }
        except Exception as e:
            logger.error(f"Error executing script: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_content(self, page_id: str) -> Dict[str, Any]:
        """Get page HTML content"""
        if page_id not in self.pages:
            return {"status": "error", "error": "Page not found"}
        
        try:
            page = self.pages[page_id]["page"]
            content = await page.content()
            
            logger.info(f"Got content of page {page_id}")
            return {
                "status": "ok",
                "content": content,
                "url": page.url,
                "title": await page.title()
            }
        except Exception as e:
            logger.error(f"Error getting content: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_text(self, page_id: str) -> Dict[str, Any]:
        """Get page text content"""
        if page_id not in self.pages:
            return {"status": "error", "error": "Page not found"}
        
        try:
            page = self.pages[page_id]["page"]
            text = await page.inner_text('body')
            
            logger.info(f"Got text of page {page_id}")
            return {
                "status": "ok",
                "text": text
            }
        except Exception as e:
            logger.error(f"Error getting text: {e}")
            return {"status": "error", "error": str(e)}
    
    async def click(self, page_id: str, selector: str) -> Dict[str, Any]:
        """Click an element"""
        if page_id not in self.pages:
            return {"status": "error", "error": "Page not found"}
        
        try:
            page = self.pages[page_id]["page"]
            element = await page.query_selector(selector)
            if element:
                await element.click()
                logger.info(f"Clicked element {selector} on page {page_id}")
                return {"status": "ok"}
            else:
                return {"status": "error", "error": f"Element not found: {selector}"}
        except Exception as e:
            logger.error(f"Error clicking element: {e}")
            return {"status": "error", "error": str(e)}
    
    async def fill(self, page_id: str, selector: str, value: str) -> Dict[str, Any]:
        """Fill a form input"""
        if page_id not in self.pages:
            return {"status": "error", "error": "Page not found"}
        
        try:
            page = self.pages[page_id]["page"]
            await page.fill(selector, value)
            logger.info(f"Filled {selector} with {value} on page {page_id}")
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"Error filling form: {e}")
            return {"status": "error", "error": str(e)}
    
    async def reload(self, page_id: str) -> Dict[str, Any]:
        """Reload a page"""
        if page_id not in self.pages:
            return {"status": "error", "error": "Page not found"}
        
        try:
            page = self.pages[page_id]["page"]
            await page.reload()
            logger.info(f"Reloaded page {page_id}")
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"Error reloading page: {e}")
            return {"status": "error", "error": str(e)}
    
    async def go_back(self, page_id: str) -> Dict[str, Any]:
        """Go back in navigation history"""
        if page_id not in self.pages:
            return {"status": "error", "error": "Page not found"}
        
        try:
            page = self.pages[page_id]["page"]
            await page.go_back()
            logger.info(f"Went back on page {page_id}")
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"Error going back: {e}")
            return {"status": "error", "error": str(e)}
    
    async def go_forward(self, page_id: str) -> Dict[str, Any]:
        """Go forward in navigation history"""
        if page_id not in self.pages:
            return {"status": "error", "error": "Page not found"}
        
        try:
            page = self.pages[page_id]["page"]
            await page.go_forward()
            logger.info(f"Went forward on page {page_id}")
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"Error going forward: {e}")
            return {"status": "error", "error": str(e)}
    
    def is_initialized(self) -> bool:
        """Check if browser is initialized"""
        return self._initialized
