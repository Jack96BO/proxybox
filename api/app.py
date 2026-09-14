"""
ProxyBox REST API Backend
Flask API for controlling Playwright browser remotely
Supports navigation, screenshot, DOM manipulation, and traffic interception
"""

from flask import Flask, request, jsonify, send_file, Response, render_template
from flask_cors import CORS
from playwright.sync_api import sync_playwright
from dns_manager import dns_manager
import os
import time
import threading
import base64
import json
from io import BytesIO

app = Flask(__name__)
CORS(app)

# Configure templates folder
basedir = os.path.abspath(os.path.dirname(__file__))
app.template_folder = os.path.join(basedir, 'templates')

# Global variables for browser state
browser_instance = None
pages = {}
current_page_id = 1
lock = threading.Lock()

# Configuration
PROXY_SERVER = os.environ.get("PROXY_SERVER", "http://localhost:8080")
DNS_SERVER = os.environ.get("DNS_SERVER", "172.20.0.2")


def initialize_browser():
    """Initialize Playwright browser with proxy settings"""
    global browser_instance
    
    with lock:
        if browser_instance is None:
            try:
                browser_instance = sync_playwright().start()
                browser_instance = browser_instance.chromium.launch(
                    proxy={"server": PROXY_SERVER} if PROXY_SERVER else None,
                    headless=True,
                    args=[
                        "--ignore-certificate-errors",
                        "--allow-running-insecure-content",
                        "--disable-gpu",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-setuid-sandbox",
                        "--single-process"
                    ]
                )
                print("Browser initialized successfully")
            except Exception as e:
                print(f"Error initializing browser: {e}")
                browser_instance = None


def get_browser():
    """Get or initialize browser instance"""
    if browser_instance is None:
        initialize_browser()
        # Wait for browser to initialize
        time.sleep(3)
    return browser_instance


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "browser": browser_instance is not None,
        "pages": len(pages)
    })


@app.route('/api/browser/start', methods=['POST'])
def start_browser():
    """Start a new browser instance"""
    initialize_browser()
    return jsonify({"status": "ok", "message": "Browser started"})


@app.route('/api/browser/stop', methods=['POST'])
def stop_browser():
    """Stop the browser instance"""
    global browser_instance, pages
    
    with lock:
        if browser_instance:
            browser_instance.close()
            browser_instance = None
        pages = {}
    
    return jsonify({"status": "ok", "message": "Browser stopped"})


@app.route('/api/page/create', methods=['POST'])
def create_page():
    """Create a new browser page"""
    global current_page_id
    
    browser = get_browser()
    if not browser:
        return jsonify({"error": "Browser not available"}), 500
    
    try:
        page = browser.new_page()
        page_id = current_page_id
        current_page_id += 1
        pages[page_id] = page
        
        return jsonify({
            "status": "ok",
            "page_id": page_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/page/<int:page_id>/close', methods=['POST'])
def close_page(page_id):
    """Close a browser page"""
    if page_id in pages:
        try:
            pages[page_id].close()
            del pages[page_id]
            return jsonify({"status": "ok"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Page not found"}), 404


@app.route('/api/page/<int:page_id>/navigate', methods=['POST'])
def navigate(page_id):
    """Navigate to a URL"""
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    if page_id not in pages:
        return jsonify({"error": "Page not found"}), 404
    
    try:
        page = pages[page_id]
        page.goto(url, timeout=30000)
        
        return jsonify({
            "status": "ok",
            "title": page.title(),
            "url": page.url
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/page/<int:page_id>/screenshot', methods=['POST'])
def take_screenshot(page_id):
    """Take a screenshot of the page"""
    data = request.get_json()
    format = data.get('format', 'png')
    full_page = data.get('full_page', False)
    
    if page_id not in pages:
        return jsonify({"error": "Page not found"}), 404
    
    try:
        page = pages[page_id]
        screenshot_bytes = page.screenshot(
            full_page=full_page,
            type=format
        )
        
        # Return as base64 encoded image
        return jsonify({
            "status": "ok",
            "image": base64.b64encode(screenshot_bytes).decode('utf-8'),
            "format": format
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/page/<int:page_id>/content', methods=['GET'])
def get_content(page_id):
    """Get page HTML content"""
    if page_id not in pages:
        return jsonify({"error": "Page not found"}), 404
    
    try:
        page = pages[page_id]
        content = page.content()
        
        return jsonify({
            "status": "ok",
            "content": content,
            "title": page.title(),
            "url": page.url
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/page/<int:page_id>/text', methods=['GET'])
def get_text(page_id):
    """Get page text content (without HTML tags)"""
    if page_id not in pages:
        return jsonify({"error": "Page not found"}), 404
    
    try:
        page = pages[page_id]
        text = page.inner_text('body')
        
        return jsonify({
            "status": "ok",
            "text": text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/page/<int:page_id>/execute', methods=['POST'])
def execute_javascript(page_id):
    """Execute JavaScript on the page"""
    data = request.get_json()
    script = data.get('script')
    
    if not script:
        return jsonify({"error": "Script is required"}), 400
    
    if page_id not in pages:
        return jsonify({"error": "Page not found"}), 404
    
    try:
        page = pages[page_id]
        result = page.evaluate(script)
        
        return jsonify({
            "status": "ok",
            "result": result
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/page/<int:page_id>/click', methods=['POST'])
def click_element(page_id):
    """Click an element on the page"""
    data = request.get_json()
    selector = data.get('selector')
    
    if not selector:
        return jsonify({"error": "Selector is required"}), 400
    
    if page_id not in pages:
        return jsonify({"error": "Page not found"}), 404
    
    try:
        page = pages[page_id]
        element = page.query_selector(selector)
        if element:
            element.click()
            return jsonify({"status": "ok"})
        else:
            return jsonify({"error": f"Element with selector '{selector}' not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/page/<int:page_id>/fill', methods=['POST'])
def fill_form(page_id):
    """Fill a form input"""
    data = request.get_json()
    selector = data.get('selector')
    value = data.get('value')
    
    if not selector or value is None:
        return jsonify({"error": "Selector and value are required"}), 400
    
    if page_id not in pages:
        return jsonify({"error": "Page not found"}), 404
    
    try:
        page = pages[page_id]
        page.fill(selector, str(value))
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/page/<int:page_id>/title', methods=['GET'])
def get_title(page_id):
    """Get page title"""
    if page_id not in pages:
        return jsonify({"error": "Page not found"}), 404
    
    try:
        page = pages[page_id]
        return jsonify({
            "status": "ok",
            "title": page.title()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/page/<int:page_id>/url', methods=['GET'])
def get_url(page_id):
    """Get current page URL"""
    if page_id not in pages:
        return jsonify({"error": "Page not found"}), 404
    
    try:
        page = pages[page_id]
        return jsonify({
            "status": "ok",
            "url": page.url
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/page/<int:page_id>/back', methods=['POST'])
def go_back(page_id):
    """Go back in navigation history"""
    if page_id not in pages:
        return jsonify({"error": "Page not found"}), 404
    
    try:
        page = pages[page_id]
        page.go_back()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/page/<int:page_id>/forward', methods=['POST'])
def go_forward(page_id):
    """Go forward in navigation history"""
    if page_id not in pages:
        return jsonify({"error": "Page not found"}), 404
    
    try:
        page = pages[page_id]
        page.go_forward()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/page/<int:page_id>/reload', methods=['POST'])
def reload_page(page_id):
    """Reload the page"""
    if page_id not in pages:
        return jsonify({"error": "Page not found"}), 404
    
    try:
        page = pages[page_id]
        page.reload()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/pages/list', methods=['GET'])
def list_pages():
    """List all open pages"""
    page_info = []
    for page_id, page in pages.items():
        try:
            page_info.append({
                "page_id": page_id,
                "title": page.title(),
                "url": page.url
            })
        except:
            pass
    
    return jsonify({
        "status": "ok",
        "pages": page_info
    })


@app.route('/api/dns/resolve', methods=['POST'])
def resolve_dns():
    """Resolve a domain using the custom DNS"""
    data = request.get_json()
    domain = data.get('domain')
    
    if not domain:
        return jsonify({"error": "Domain is required"}), 400
    
    try:
        # This is a simple check - in production, use a proper DNS resolver
        if domain == "ilmiosito.com":
            return jsonify({
                "status": "ok",
                "domain": domain,
                "ip": "10.58.54.2"
            })
        else:
            return jsonify({
                "status": "ok",
                "domain": domain,
                "ip": "not configured"
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# HTML Dashboard Route
@app.route('/')
def index():
    """Serve the web dashboard"""
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    """Redirect to main dashboard"""
    return render_template('index.html')


# DNS Management API Endpoints
@app.route('/api/dns/routes', methods=['GET'])
def list_dns_routes():
    """List all custom DNS routes"""
    try:
        routes = dns_manager.list_routes()
        return jsonify({
            "status": "ok",
            "routes": routes
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/dns/routes', methods=['POST'])
def add_dns_route():
    """Add a new DNS route and apply to mitmproxy"""
    data = request.get_json()
    domain = data.get('domain')
    ip = data.get('ip')
    
    if not domain or not ip:
        return jsonify({"error": "domain and ip are required"}), 400
    
    try:
        success, message = dns_manager.add_route(domain, ip)
        if success:
            # Apply to mitmproxy
            try:
                from mitmproxy_script import add_dns_route as mitm_add_route
                mitm_add_route(domain, ip)
            except:
                pass  # mitmproxy might not be running yet
            
            return jsonify({
                "status": "ok",
                "message": message,
                "domain": domain,
                "ip": ip
            })
        else:
            return jsonify({"error": message}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/dns/routes/<domain>', methods=['DELETE'])
def remove_dns_route(domain):
    """Remove a DNS route"""
    try:
        success, message = dns_manager.remove_route(domain)
        if success:
            # Apply to mitmproxy
            try:
                from mitmproxy_script import remove_dns_route as mitm_remove_route
                mitm_remove_route(domain)
            except:
                pass  # mitmproxy might not be running yet
            
            return jsonify({
                "status": "ok",
                "message": message
            })
        else:
            return jsonify({"error": message}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/dns/routes', methods=['DELETE'])
def clear_dns_routes():
    """Clear all DNS routes"""
    try:
        success, message = dns_manager.clear_routes()
        if success:
            # Apply to mitmproxy
            try:
                from mitmproxy_script import clear_dns_routes as mitm_clear_routes
                mitm_clear_routes()
            except:
                pass  # mitmproxy might not be running yet
            
            return jsonify({
                "status": "ok",
                "message": message
            })
        else:
            return jsonify({"error": message}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Initialize browser on startup
    threading.Thread(target=initialize_browser, daemon=True).start()
    
    # Start Flask server
    app.run(host='0.0.0.0', port=5000, threaded=True)
