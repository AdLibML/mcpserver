import httpx
from fastmcp import FastMCP
from fastapi import FastAPI, Request

from fastapi.responses import JSONResponse
import asyncio
import signal
import sys
from typing import List, Dict, Any
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.sse
import mcp.server.stdio
from mcp.server.sse import SseServerTransport
from load_dotenv import load_dotenv
import os
import uvicorn
from src.utils.utils import register_mcp_router
from src.utils.setup_logger import get_logger

logger = get_logger("math_server")

load_dotenv()

mode = os.environ.get("MODE", "local")

print(f"Running in {mode} mode")

if mode == "local":
    transport = "stdio"
else:
    transport = "sse"

# -----------------------------------------------------------------------------
app = FastAPI()
mcp = FastMCP("math")          # server name visible to LLM clients

@mcp.tool()
def add(a: int, b: int) -> int:
    """
    Adds two integers and returns the result.

    Args:
        a (int): The first integer.
        b (int): The second integer.

    Returns:
        int: The sum of the two integers.
    """
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """
    Multiplies two integers and returns the result.

    Args:
        a (int): The first integer.
        b (int): The second integer.

    Returns:
        int: The product of the two integers.
    """
    return a * b

if mode == "local":
    if __name__ == "__main__":
        mcp.run(transport=transport)
else:
    if __name__ == "__main__":
        
        register_mcp_router(app, mcp, "/mcp")
        PORT = int(os.getenv("PORT_MATH_SERVER", 5001))
        logger.info(f"Starting math MCP server in production (SSE) mode on port {PORT}.")
        uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info") 
        # mcp.run(transport=transport)
