FROM python:3.12-slim

# Install Chromium for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium chromium-common \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir ".[browser]" \
    && playwright install chromium --with-deps

ENV TRANSPORT=streamable-http
ENV HOST=0.0.0.0
ENV PORT=30001

EXPOSE 30001
CMD ["python", "-m", "mcp_server_fetch", "--transport", "streamable-http", "--port", "30001"]
