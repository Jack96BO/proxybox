FROM python:3.10-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    git \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install playwright mitmproxy

# Install browsers for Playwright
RUN playwright install

# Copy scripts
COPY scripts/mitmproxy_script.py /app/mitmproxy_script.py
COPY scripts/playwright_script.py /app/playwright_script.py

# Set working directory
WORKDIR /app

# Start mitmproxy and playwright
CMD ["sh", "-c", "mitmproxy -s mitmproxy_script.py --listen-port 8080 & python playwright_script.py"]
