#!/bin/bash

# Start script for ProxyBox
# Orchestrates all services: Chromium, Mitmproxy, Flask API

set -e

echo "=========================================="
echo "  ProxyBox - Starting Services"
echo "=========================================="

# Configuration
CDP_PORT=${CDP_PORT:-9222}
MITMPROXY_PORT=${MITMPROXY_PORT:-8080}
FLASK_PORT=${FLASK_PORT:-5000}
PROXY_SERVER="http://127.0.0.1:${MITMPROXY_PORT}"

# Ensure data directory exists
mkdir -p /data/chromium

# 1. Start Mitmproxy
echo "[1/3] Starting Mitmproxy on port ${MITMPROXY_PORT}..."
mitmdump -s /app/api/mitmproxy/addon.py \
    --listen-port "$MITMPROXY_PORT" \
    --no-http2 \
    --ssl-insecure \
    &
MITMPROXY_PID=$!
echo "Mitmproxy started (PID: $MITMPROXY_PID)"

# Wait for Mitmproxy to initialize
sleep 3

# Check if Mitmproxy is running
if ! kill -0 $MITMPROXY_PID 2>/dev/null; then
    echo "ERROR: Mitmproxy failed to start"
    exit 1
fi

# 2. Start Chromium
echo "[2/3] Starting Chromium with CDP on port ${CDP_PORT}..."
/app/scripts/start-chromium.sh &
CHROMIUM_PID=$!
echo "Chromium started (PID: $CHROMIUM_PID)"

# Wait for Chromium to initialize
sleep 5

# Check if Chromium is running
if ! kill -0 $CHROMIUM_PID 2>/dev/null; then
    echo "ERROR: Chromium failed to start"
    kill $MITMPROXY_PID
    exit 1
fi

# 3. Start Flask API
echo "[3/3] Starting Flask API on port ${FLASK_PORT}..."
echo "All services ready!"

# Set environment variables for Flask
export PROXY_SERVER="$PROXY_SERVER"
export CDP_PORT="$CDP_PORT"
export MITMPROXY_PORT="$MITMPROXY_PORT"
export PYTHONPATH="/app:$PYTHONPATH"

# Change to the correct directory
cd /app

# Start Flask with Gunicorn
exec gunicorn --bind 0.0.0.0:$FLASK_PORT --workers 1 --threads 1 --timeout 300 api.app:app
