import os
import logging
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_mcp_tools import convert_mcp_to_langchain_tools
from langchain_ollama import ChatOllama
import asyncio
from load_dotenv import load_dotenv

load_dotenv()

# Configure logging for the agent
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("agent")

mode = os.environ.get("MODE", "local")

if mode == "local":
    transport = "stdio"
else:
    transport = "sse"

model = ChatOllama(model="qwen2.5:7b")

if mode == "local":
    server_params = {
        "math": {
            "command": "python",
            "args": ["/Users/garyj/Code/mcpserver/src/servers/math_server.py"],
            "transport": transport,
        },
        "weather": {
            "command": "python",
            "args": ["/Users/garyj/Code/mcpserver/src/servers/weather_server.py"],
            "transport": transport,
        }
    }
else:
    server_params = {
        "math": {
            "command": "python",
            "url": os.environ.get("MATH_URL", "http://localhost:5001/mcp/sse"),
            "transport": transport,
        },
        "weather": {
            "command": "python",
            "url": os.environ.get("WEATHER_URL", "http://localhost:5000/mcp/sse"),
            "transport": transport,
        }
    }

async def main(query: str):
    logger.info("Agent starting with query: %s", query)
    async with MultiServerMCPClient(server_params) as client:
        agent = create_react_agent(model, client.get_tools())
        response = await agent.ainvoke({"messages": query})
        logger.info("Agent received response: %s", response)
    return response

if __name__ == "__main__":
    query = "What is (3+5) * 4 - 13"
    response = asyncio.run(main(query))
    print(response)
