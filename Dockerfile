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

ENV TRANSPORT=sse
ENV HOST=0.0.0.0
ENV PORT=8080

EXPOSE 8080
CMD ["python", "-m", "mcp_server_fetch", "--transport", "sse", "--port", "8080"]
