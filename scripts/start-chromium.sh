#!/bin/bash

# Start Chromium standalone with CDP support
# This script is used inside the Docker container

set -e

echo "Starting Chromium standalone..."

# Configuration
CDP_PORT=${CDP_PORT:-9222}
PROXY_SERVER=${PROXY_SERVER:-http://127.0.0.1:8080}
USER_DATA_DIR=${USER_DATA_DIR:-"/data/chromium"}

# Ensure user data directory exists
mkdir -p "$USER_DATA_DIR"

# Chromium command
CHROMIUM_CMD=(
    chromium
    --remote-debugging-port="$CDP_PORT"
    --user-data-dir="$USER_DATA_DIR"
    --headless=new
    --proxy-server="$PROXY_SERVER"
    --no-sandbox
    --disable-setuid-sandbox
    --disable-gpu
    --disable-dev-shm-usage
    --disable-software-rasterizer
    --disable-background-networking
    --disable-background-timer-throttling
    --disable-backgrounding-occluded-windows
    --disable-breakpad
    --disable-client-side-phishing-detection
    --disable-component-extensions-with-background-pages
    --disable-default-apps
    --disable-extensions
    --disable-hang-monitor
    --disable-ipc-flooding-protection
    --disable-popup-blocking
    --disable-prompt-on-repost
    --disable-renderer-backgrounding
    --disable-sync
    --metrics-recording-only
    --mute-audio
    --use-gl=swiftshader
    --ignore-certificate-errors
    --ignore-certificate-errors-spki-list
    --allow-running-insecure-content
)

echo "Chromium command: ${CHROMIUM_CMD[*]}"

exec "${CHROMIUM_CMD[@]}"
