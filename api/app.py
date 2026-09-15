"""
ProxyBox - Control Plane API
Architettura: Chromium Standalone + CDP + Playwright + Mitmproxy

Flask API per il controllo remoto del browser tramite Chrome DevTools Protocol (CDP)
"""

import os
import sys
import logging
import time
from typing import Optional, Dict, Any
from functools import wraps

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================
CDP_PORT = int(os.environ.get("CDP_PORT", 9222))
MITMPROXY_PORT = int(os.environ.get("MITMPROXY_PORT", 8080))
FLASK_PORT = int(os.environ.get("FLASK_PORT", 5000))
PROXY_SERVER = os.environ.get("PROXY_SERVER", f"http://127.0.0.1:{MITMPROXY_PORT}")
USER_DATA_DIR = os.environ.get("USER_DATA_DIR", "/data/chromium")

# ============================================================================
# Import Modules
# ============================================================================
# Browser Manager (Chromium + CDP + Playwright)
from api.browser.manager import BrowserManager

# Network Manager (DNS + Proxy)
from api.network.dns_manager import DNSManager
from api.network.proxy_manager import ProxyManager

# Mitmproxy Addon
from api.mitmproxy.addon import MitmproxyAddon

# ============================================================================
# Initialize Components
# ============================================================================
# Browser Manager
browser_manager = BrowserManager(
    cdp_port=CDP_PORT,
    proxy_server=PROXY_SERVER,
    user_data_dir=USER_DATA_DIR
)

# DNS Manager
dns_manager = DNSManager()

# Proxy Manager
proxy_manager = ProxyManager(
    port=MITMPROXY_PORT,
    script_path="/app/api/mitmproxy/addon.py"
)

# Mitmproxy Addon
mitmproxy_addon = MitmproxyAddon()

# Connect DNS Manager to Mitmproxy
dns_manager.set_mitmproxy_addon(mitmproxy_addon)

# ============================================================================
# Flask App
# ============================================================================
app = Flask(__name__)
CORS(app)

# Configure templates
basedir = os.path.abspath(os.path.dirname(__file__))
app.template_folder = os.path.join(basedir, 'templates')


# ============================================================================
# Async Helper for Flask
# ============================================================================
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Create executor for running async functions in sync context
executor = ThreadPoolExecutor(max_workers=1)

def run_async(func, *args, **kwargs):
    """Run async function in sync context"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(func(*args, **kwargs))
    finally:
        loop.close()


# ============================================================================
# Helper Functions
# ============================================================================
def ensure_browser():
    """Ensure browser is initialized (sync wrapper)"""
    if not browser_manager.is_initialized():
        success = run_async(browser_manager.start)
        if not success:
            logger.error("Failed to initialize browser")
            return False
    return True


# ============================================================================
# API Endpoints - Health & Status
# ============================================================================
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    browser_status = browser_manager.is_initialized()
    proxy_status = proxy_manager.is_running()
    
    return jsonify({
        "status": "ok",
        "browser": browser_status,
        "proxy": proxy_status,
        "cdp_port": CDP_PORT,
        "mitmproxy_port": MITMPROXY_PORT,
        "flask_port": FLASK_PORT
    })


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get detailed status"""
    browser_status = browser_manager.is_initialized()
    proxy_status = proxy_manager.is_running()
    
    # Get browser stats
    browser_stats = {
        "pages": len(browser_manager.pages),
        "contexts": len(browser_manager.contexts)
    }
    
    # Get proxy stats
    proxy_stats = {
        "running": proxy_status,
        "port": MITMPROXY_PORT,
        "url": proxy_manager.get_proxy_url()
    }
    
    # Get DNS routes
    dns_routes = dns_manager.list_routes()
    
    return jsonify({
        "status": "ok",
        "browser": browser_status,
        "proxy": proxy_status,
        "browser_stats": browser_stats,
        "proxy_stats": proxy_stats,
        "dns_routes": dns_routes,
        "dns_routes_count": len(dns_routes)
    })


# ============================================================================
# API Endpoints - Browser Control
# ============================================================================
@app.route('/api/browser/start', methods=['POST'])
def start_browser():
    """Start the browser"""
    success = run_async(browser_manager.start)
    if success:
        return jsonify({"status": "ok", "message": "Browser started"})
    else:
        return jsonify({"status": "error", "error": "Failed to start browser"}), 500


@app.route('/api/browser/stop', methods=['POST'])
def stop_browser():
    """Stop the browser"""
    success = run_async(browser_manager.stop)
    if success:
        return jsonify({"status": "ok", "message": "Browser stopped"})
    else:
        return jsonify({"status": "error", "error": "Failed to stop browser"}), 500


@app.route('/api/browser/restart', methods=['POST'])
def restart_browser():
    """Restart the browser"""
    success = run_async(browser_manager.restart)
    if success:
        return jsonify({"status": "ok", "message": "Browser restarted"})
    else:
        return jsonify({"status": "error", "error": "Failed to restart browser"}), 500


# ============================================================================
# API Endpoints - Context Management
# ============================================================================
@app.route('/api/context/create', methods=['POST'])
def create_context():
    """Create a new browser context"""
    if not ensure_browser():
        return jsonify({"status": "error", "error": "Browser not available"}), 500
    
    data = request.get_json()
    name = data.get('name') if data else None
    
    result = run_async(browser_manager.create_context, name)
    return jsonify(result), 200 if result.get('status') == 'ok' else 400


# ============================================================================
# API Endpoints - Page Management
# ============================================================================
@app.route('/api/page/create', methods=['POST'])
def create_page():
    """Create a new page"""
    if not ensure_browser():
        return jsonify({"status": "error", "error": "Browser not available"}), 500
    
    data = request.get_json() or {}
    context_id = data.get('context_id')
    url = data.get('url')
    
    result = run_async(browser_manager.create_page, context_id, url)
    return jsonify(result), 200 if result.get('status') == 'ok' else 400


@app.route('/api/page/<page_id>/close', methods=['POST'])
def close_page(page_id: str):
    """Close a page"""
    if not ensure_browser():
        return jsonify({"status": "error", "error": "Browser not available"}), 500
    
    result = run_async(browser_manager.close_page, page_id)
    return jsonify(result), 200 if result.get('status') == 'ok' else 404


@app.route('/api/pages/list', methods=['GET'])
def list_pages():
    """List all pages"""
    if not ensure_browser():
        return jsonify({"status": "error", "error": "Browser not available"}), 500
    
    result = run_async(browser_manager.list_pages)
    return jsonify(result)


# ============================================================================
# API Endpoints - Navigation
# ============================================================================
@app.route('/api/page/<page_id>/navigate', methods=['POST'])
def navigate(page_id: str):
    """Navigate to a URL"""
    if not ensure_browser():
        return jsonify({"status": "error", "error": "Browser not available"}), 500
    
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"status": "error", "error": "URL is required"}), 400
    
    url = data['url']
    wait_until = data.get('wait_until', 'domcontentloaded')
    
    result = run_async(browser_manager.navigate, page_id, url, wait_until)
    return jsonify(result), 200 if result.get('status') == 'ok' else 400


@app.route('/api/page/<page_id>/reload', methods=['POST'])
def reload_page(page_id: str):
    """Reload a page"""
    if not ensure_browser():
        return jsonify({"status": "error", "error": "Browser not available"}), 500
    
    result = run_async(browser_manager.reload, page_id)
    return jsonify(result), 200 if result.get('status') == 'ok' else 404


@app.route('/api/page/<page_id>/back', methods=['POST'])
def go_back(page_id: str):
    """Go back in navigation history"""
    if not ensure_browser():
        return jsonify({"status": "error", "error": "Browser not available"}), 500
    
    result = run_async(browser_manager.go_back, page_id)
    return jsonify(result), 200 if result.get('status') == 'ok' else 404


@app.route('/api/page/<page_id>/forward', methods=['POST'])
def go_forward(page_id: str):
    """Go forward in navigation history"""
    if not ensure_browser():
        return jsonify({"status": "error", "error": "Browser not available"}), 500
    
    result = run_async(browser_manager.go_forward, page_id)
    return jsonify(result), 200 if result.get('status') == 'ok' else 404


# ============================================================================
# API Endpoints - Content
# ============================================================================
@app.route('/api/page/<page_id>/screenshot', methods=['POST'])
def take_screenshot(page_id: str):
    """Take a screenshot of a page"""
    if not ensure_browser():
        return jsonify({"status": "error", "error": "Browser not available"}), 500
    
    data = request.get_json() or {}
    full_page = data.get('full_page', False)
    format = data.get('format', 'png')
    
    result = run_async(browser_manager.screenshot, page_id, full_page, format)
    return jsonify(result), 200 if result.get('status') == 'ok' else 404


@app.route('/api/page/<page_id>/content', methods=['GET'])
def get_content(page_id: str):
    """Get page HTML content"""
    if not ensure_browser():
        return jsonify({"status": "error", "error": "Browser not available"}), 500
    
    result = run_async(browser_manager.get_content, page_id)
    return jsonify(result), 200 if result.get('status') == 'ok' else 404


@app.route('/api/page/<page_id>/text', methods=['GET'])
def get_text(page_id: str):
    """Get page text content"""
    if not ensure_browser():
        return jsonify({"status": "error", "error": "Browser not available"}), 500
    
    result = run_async(browser_manager.get_text, page_id)
    return jsonify(result), 200 if result.get('status') == 'ok' else 404


# ============================================================================
# API Endpoints - JavaScript Execution
# ============================================================================
@app.route('/api/page/<page_id>/execute', methods=['POST'])
def execute_script(page_id: str):
    """Execute JavaScript on a page"""
    if not ensure_browser():
        return jsonify({"status": "error", "error": "Browser not available"}), 500
    
    data = request.get_json()
    if not data or 'script' not in data:
        return jsonify({"status": "error", "error": "Script is required"}), 400
    
    script = data['script']
    result = run_async(browser_manager.execute_script, page_id, script)
    return jsonify(result), 200 if result.get('status') == 'ok' else 404


# ============================================================================
# API Endpoints - Element Interaction
# ============================================================================
@app.route('/api/page/<page_id>/click', methods=['POST'])
def click_element(page_id: str):
    """Click an element on a page"""
    if not ensure_browser():
        return jsonify({"status": "error", "error": "Browser not available"}), 500
    
    data = request.get_json()
    if not data or 'selector' not in data:
        return jsonify({"status": "error", "error": "Selector is required"}), 400
    
    selector = data['selector']
    result = run_async(browser_manager.click, page_id, selector)
    return jsonify(result), 200 if result.get('status') == 'ok' else 404


@app.route('/api/page/<page_id>/fill', methods=['POST'])
def fill_form(page_id: str):
    """Fill a form input"""
    if not ensure_browser():
        return jsonify({"status": "error", "error": "Browser not available"}), 500
    
    data = request.get_json()
    if not data or 'selector' not in data or 'value' not in data:
        return jsonify({"status": "error", "error": "Selector and value are required"}), 400
    
    selector = data['selector']
    value = data['value']
    result = run_async(browser_manager.fill, page_id, selector, value)
    return jsonify(result), 200 if result.get('status') == 'ok' else 404


# ============================================================================
# API Endpoints - DNS Management
# ============================================================================
@app.route('/api/dns/routes', methods=['GET'])
def list_dns_routes():
    """List all DNS routes"""
    try:
        routes = dns_manager.list_routes()
        return jsonify({
            "status": "ok",
            "routes": routes,
            "count": len(routes)
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/api/dns/routes', methods=['POST'])
def add_dns_route():
    """Add a new DNS route"""
    data = request.get_json()
    if not data or 'domain' not in data or 'ip' not in data:
        return jsonify({"status": "error", "error": "domain and ip are required"}), 400
    
    domain = data['domain']
    ip = data['ip']
    
    try:
        success, message = dns_manager.add_route(domain, ip)
        if success:
            return jsonify({
                "status": "ok",
                "message": message,
                "domain": domain,
                "ip": ip
            })
        else:
            return jsonify({"status": "error", "error": message}), 400
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/api/dns/routes/<domain>', methods=['DELETE'])
def remove_dns_route(domain: str):
    """Remove a DNS route"""
    try:
        success, message = dns_manager.remove_route(domain)
        if success:
            return jsonify({"status": "ok", "message": message})
        else:
            return jsonify({"status": "error", "error": message}), 400
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/api/dns/routes', methods=['DELETE'])
def clear_dns_routes():
    """Clear all DNS routes"""
    try:
        success, message = dns_manager.clear_routes()
        if success:
            return jsonify({"status": "ok", "message": message})
        else:
            return jsonify({"status": "error", "error": message}), 400
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


# ============================================================================
# API Endpoints - Proxy Management
# ============================================================================
@app.route('/api/proxy/start', methods=['POST'])
def start_proxy():
    """Start Mitmproxy"""
    success = proxy_manager.start()
    if success:
        return jsonify({"status": "ok", "message": "Mitmproxy started"})
    else:
        return jsonify({"status": "error", "error": "Failed to start Mitmproxy"}), 500


@app.route('/api/proxy/stop', methods=['POST'])
def stop_proxy():
    """Stop Mitmproxy"""
    success = proxy_manager.stop()
    if success:
        return jsonify({"status": "ok", "message": "Mitmproxy stopped"})
    else:
        return jsonify({"status": "error", "error": "Failed to stop Mitmproxy"}), 500


@app.route('/api/proxy/restart', methods=['POST'])
def restart_proxy():
    """Restart Mitmproxy"""
    success = proxy_manager.restart()
    if success:
        return jsonify({"status": "ok", "message": "Mitmproxy restarted"})
    else:
        return jsonify({"status": "error", "error": "Failed to restart Mitmproxy"}), 500


@app.route('/api/proxy/status', methods=['GET'])
def get_proxy_status():
    """Get Mitmproxy status"""
    return jsonify({
        "status": "ok",
        "running": proxy_manager.is_running(),
        "port": MITMPROXY_PORT,
        "url": proxy_manager.get_proxy_url()
    })


# ============================================================================
# Dashboard Routes
# ============================================================================
@app.route('/')
def index():
    """Serve the web dashboard"""
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    """Redirect to main dashboard"""
    return render_template('index.html')


# ============================================================================
# Main
# ============================================================================
if __name__ == '__main__':
    logger.info(f"Starting ProxyBox API on port {FLASK_PORT}")
    logger.info(f"CDP Port: {CDP_PORT}")
    logger.info(f"Mitmproxy Port: {MITMPROXY_PORT}")
    logger.info(f"Proxy Server: {PROXY_SERVER}")
    logger.info(f"User Data Dir: {USER_DATA_DIR}")
    
    # Start proxy manager
    proxy_manager.start()
    
    # Start Flask
    app.run(host='0.0.0.0', port=FLASK_PORT, threaded=True)
