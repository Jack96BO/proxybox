"""
Playwright script for browser automation with proxy support
- Uses mitmproxy for traffic interception
- Supports DNS redirection via dnsmasq
- Can be used for scraping, testing, and automation
"""

from playwright.sync_api import sync_playwright
import time
import os


def main():
    """Main function to run browser automation"""
    
    # Wait for mitmproxy to start
    print("Waiting for mitmproxy to start...")
    time.sleep(3)
    
    # DNS server configuration (from environment or default)
    dns_server = os.environ.get("DNS_SERVER", "172.20.0.2")
    proxy_server = os.environ.get("PROXY_SERVER", "http://localhost:8080")
    
    print(f"Using DNS server: {dns_server}")
    print(f"Using proxy server: {proxy_server}")
    
    with sync_playwright() as p:
        # Launch browser with proxy and DNS configuration
        browser = p.chromium.launch(
            proxy={"server": proxy_server},
            headless=False,  # Set to True for headless mode
            args=[
                f"--dns-servers={dns_server}",
                "--ignore-certificate-errors",
                "--allow-running-insecure-content",
            ]
        )
        
        try:
            # Create a new page
            page = browser.new_page()
            
            # Example 1: Navigate to ilmiosito.com (will be redirected via DNS)
            print("\n1. Testing DNS redirection to ilmiosito.com...")
            page.goto("http://ilmiosito.com")
            print(f"Title: {page.title()}")
            print(f"URL: {page.url}")
            
            # Take a screenshot
            page.screenshot(path="/app/screenshot_ilmiosito.png")
            print("Screenshot saved to /app/screenshot_ilmiosito.png")
            
            # Example 2: Scrape content
            print("\n2. Scraping content from ilmiosito.com...")
            content = page.content()
            print(f"Content length: {len(content)} characters")
            
            # Example 3: Modify page content
            print("\n3. Modifying page content...")
            page.evaluate("""
                document.body.innerHTML = '<h1>Modified by Playwright!</h1>' + document.body.innerHTML;
            """)
            
            # Take another screenshot
            page.screenshot(path="/app/screenshot_modified.png")
            print("Modified screenshot saved to /app/screenshot_modified.png")
            
            # Example 4: Navigate to another site
            print("\n4. Testing regular navigation to example.com...")
            page.goto("http://example.com")
            print(f"Title: {page.title()}")
            print(f"URL: {page.url}")
            
            # Example 5: Get all links on the page
            print("\n5. Extracting links from example.com...")
            links = page.query_selector_all("a")
            print(f"Found {len(links)} links")
            for i, link in enumerate(links[:5]):  # Print first 5 links
                href = link.get_attribute("href")
                text = link.inner_text()
                print(f"  Link {i+1}: {text} -> {href}")
            
            # Keep the browser open for a while (for manual inspection)
            print("\n6. Keeping browser open for 60 seconds...")
            time.sleep(60)
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()
            print("\nBrowser closed.")


if __name__ == "__main__":
    main()
