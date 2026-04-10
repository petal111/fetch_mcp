# mcp-server-fetch

A Model Context Protocol (MCP) server for fetching web content and converting it to clean Markdown.

一个基于 MCP 协议的网页内容抓取服务器，支持将网页内容提取为干净的 Markdown 格式。

## Features / 功能特性

- **Three-tier fetching strategy / 三层抓取策略**:
  - **L1**: httpx (fast, lightweight) — works without a browser
  - **L2**: Playwright headless browser — for JavaScript-rendered pages
  - **L3**: Playwright + stealth mode — bypasses anti-bot detection
- **HTML to Markdown / HTML 转 Markdown**: Extracts readable content and converts to Markdown
- **Image preservation / 图片保留**: Keeps image URLs in extracted content
- **robots.txt compliance / robots.txt 遵守**: Respects site crawling rules by default
- **Dual transport / 双传输模式**: Supports both STDIO and SSE transports
- **Proxy support / 代理支持**: HTTP/HTTPS proxy configuration
- **Cookie support / Cookie 支持**: Load cookies from JSON file for authenticated access

## Installation / 安装

### pip

```bash
# Basic installation (httpx-only, no browser needed)
pip install git+https://github.com/petal111/fetch_mcp.git

# With browser support (requires Chromium)
pip install "git+https://github.com/petal111/fetch_mcp.git[browser]"
playwright install chromium --with-deps
```

### uvx

```bash
uvx --from git+https://github.com/petal111/fetch_mcp.git mcp-server-fetch
```

## Usage / 使用方式

### CLI

```bash
# STDIO mode (default)
mcp-server-fetch

# SSE mode
mcp-server-fetch --transport sse --port 8080

# With options
mcp-server-fetch --ignore-robots-txt --proxy-url http://proxy:8080 --stealth
```

### CLI Arguments / 命令行参数

| Argument | Default | Description |
|----------|---------|-------------|
| `--transport` | `stdio` | Transport mode: `stdio` or `sse` |
| `--port` | `8080` | Port for SSE mode |
| `--ignore-robots-txt` | `false` | Ignore robots.txt restrictions |
| `--user-agent` | Chrome UA | Custom User-Agent string |
| `--proxy-url` | None | Proxy URL for requests |
| `--stealth` | `false` | Enable Playwright stealth mode |
| `--cookies` | None | Path to cookies JSON file |

### Environment Variables / 环境变量

| Variable | Default | Description |
|----------|---------|-------------|
| `PROXY_URL` | None | Default proxy URL |
| `IGNORE_ROBOTS_TXT` | `false` | Ignore robots.txt |
| `USER_AGENT` | Chrome UA | Default User-Agent |

## MCP Tool API

### `fetch` Tool

Fetches a URL and extracts its contents as Markdown.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string (URI) | *required* | URL to fetch |
| `max_length` | integer | `5000` | Maximum characters to return |
| `start_index` | integer | `0` | Start content from this character index |
| `raw` | boolean | `false` | Return raw content without Markdown conversion |
| `force_browser` | boolean | `false` | Force use of headless browser |

**Example (Claude Desktop config):**

```json
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/petal111/fetch_mcp.git", "mcp-server-fetch"]
    }
  }
}
```

### `fetch` Prompt

A prompt template that fetches a URL and returns its content.

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `url` | Yes | URL to fetch |

## Deployment on ModelScope MCP Hub / 魔搭 MCP 广场部署

This server supports **hosted deployment** on [ModelScope MCP Hub](https://modelscope.cn/studios/iic/MCP-Hub-Playground).

| Config | Value |
|--------|-------|
| Protocol | STDIO |
| Install | `pip install git+https://github.com/petal111/fetch_mcp.git` |
| Start command | `mcp-server-fetch` |

> **Note**: The hosted (Serverless) environment does not include Chromium, so only the httpx (L1) strategy is available. For full browser support, use Docker deployment.

## Docker Deployment / Docker 部署

For full three-tier fetching support (including Playwright):

```bash
docker build -t mcp-server-fetch .
docker run -p 8080:8080 mcp-server-fetch
```

The container runs in SSE mode on port 8080 with Chromium pre-installed.

## License

[MIT](LICENSE) Copyright 2026 petal111
