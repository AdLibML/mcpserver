import os
import logging
import httpx
from fastmcp import FastMCP
from fastapi.responses import JSONResponse
from fastapi import FastAPI
import asyncio
import signal
import sys
from typing import List, Dict, Any
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import requests
import uvicorn
from load_dotenv import load_dotenv
from models.utils import register_mcp_router

# -------------------------------------------------------------------------
# Set up logging configuration for a consistent log output across the codebase
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("weather_server")

# -------------------------------------------------------------------------
load_dotenv()

mode = os.environ.get("MODE", "local")
logger.info(f"Running in {mode} mode")

if mode == "local":
    transport = "stdio"
else:
    transport = "sse"

# -------------------------------------------------------------------------
app = FastAPI()
mcp = FastMCP("weather")  # MCP server name visible to LLM clients

tools = [{
    "type": "function",
    "name": "get_weather",
    "description": "Get current temperature for provided coordinates in celsius.",
    "parameters": {
        "type": "object",
        "properties": {
            "latitude": {"type": "number"},
            "longitude": {"type": "number"}
        },
        "required": ["latitude", "longitude"],
        "additionalProperties": False
    },
    "strict": True
}]

@mcp.tool()
async def get_weather(latitude: float, longitude: float):
    """Fetch the current temperature for given coordinates."""
    logger.info(f"Fetching weather for coordinates: latitude={latitude}, longitude={longitude}")
    try:
        response = requests.get(
            f"https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,wind_speed_10m",
                "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m"
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        res = {
            "temperature": data['current']['temperature_2m'],
            "unit": data.get('current_units', {}).get('temperature_2m', 'unknown')
        }
        logger.info(f"Weather data received: {res}")
        return res
    except Exception as e:
        logger.error("Error fetching weather data", exc_info=True)
        return {"error": str(e)}

@mcp.tool()
async def get_coordinates(location: str):
    """Get the coordinates (latitude and longitude) for a given location. This will be needed to get the weather for the location."""
    logging.info(f"Received request to get coordinates for location: {location}")
    # In a real implementation, you would perform a lookup. For now, return a placeholder.
    return tools[0]

# -------------------------------------------------------------------------
if mode == "local":
    if __name__ == "__main__":
        logger.info("Starting MCP server in local (stdio) mode.")
        mcp.run(transport=transport)
else:
    if __name__ == "__main__":
        register_mcp_router(app, mcp, "/mcp")
        PORT = int(os.getenv("PORT_WEATHER_SERVER", 5000))
        logger.info(f"Starting MCP server in production (SSE) mode on port {PORT}.")
        uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")