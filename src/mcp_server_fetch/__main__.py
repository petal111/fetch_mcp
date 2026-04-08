import argparse
import asyncio
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP Fetch Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport mode (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for SSE mode (default: 8080)",
    )
    parser.add_argument(
        "--ignore-robots-txt",
        action="store_true",
        help="Ignore robots.txt restrictions",
    )
    parser.add_argument(
        "--user-agent",
        type=str,
        default=None,
        help="Custom User-Agent string",
    )
    parser.add_argument(
        "--proxy-url",
        type=str,
        default=None,
        help="Proxy URL for requests",
    )
    parser.add_argument(
        "--stealth",
        action="store_true",
        help="Enable Playwright stealth mode",
    )
    parser.add_argument(
        "--cookies",
        type=str,
        default=None,
        help="Path to cookies JSON file",
    )

    args = parser.parse_args()

    from mcp_server_fetch.server import run_server

    asyncio.run(
        run_server(
            transport=args.transport,
            port=args.port,
            ignore_robots_txt=args.ignore_robots_txt,
            user_agent=args.user_agent,
            proxy_url=args.proxy_url,
            stealth=args.stealth,
            cookies_path=args.cookies,
        )
    )


if __name__ == "__main__":
    main()
