from __future__ import annotations

import logging

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Mount, Route

logger = logging.getLogger(__name__)


async def run_sse(server: Server, options: dict, port: int = 8080) -> None:
    """Run the MCP server using SSE transport.

    Args:
        server: Configured MCP Server instance.
        options: Server initialization options.
        port: Port to listen on.
    """
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0],
                streams[1],
                options,
                raise_exceptions=False,
            )

    async def handle_messages(request):
        await sse.handle_post_message(request.scope, request.receive, request._send)

    app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

    import uvicorn

    logger.info(f"Starting MCP Fetch Server (SSE) on port {port}")
    uvicorn_config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    uvicorn_server = uvicorn.Server(uvicorn_config)
    await uvicorn_server.serve()
