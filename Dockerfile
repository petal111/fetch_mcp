FROM python:3.12-slim

# Security: run as non-root user
RUN groupadd -r mcp && useradd -r -g mcp mcp

# Install Chromium for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium chromium-common \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir ".[browser]" \
    && playwright install chromium --with-deps \
    && chown -R mcp:mcp /app

USER mcp

ENV TRANSPORT=streamable-http
ENV HOST=0.0.0.0
ENV PORT=30001

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:30001/health')" || exit 1

EXPOSE 30001
CMD ["python", "-m", "mcp_server_fetch", "--transport", "streamable-http", "--port", "30001"]
