from fastmcp import FastMCP
from fastapi import FastAPI, Request

from mcp.server.sse import SseServerTransport
from load_dotenv import load_dotenv


def register_mcp_router(
        starlette_app: FastAPI,
        mcp_server: FastMCP,
        base_path: str,
        ):
            sse = SseServerTransport(f"{base_path}/messages/")

            async def handle_sse(request: Request) -> None:
                async with sse.connect_sse(
                    request.scope,
                    request.receive,
                    request._send,  # noqa: SLF001
                ) as (read_stream, write_stream):
                    await mcp_server._mcp_server.run(
                        read_stream,
                        write_stream,
                        mcp_server._mcp_server.create_initialization_options(),
                    )

            starlette_app.add_route(f"{base_path}/sse", handle_sse)
            starlette_app.mount(f"{base_path}/messages/", sse.handle_post_message)