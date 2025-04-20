import os
import logging
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_mcp_tools import convert_mcp_to_langchain_tools
from langchain_ollama import ChatOllama
import asyncio
from load_dotenv import load_dotenv
from src.utils.setup_logger import get_logger  # new import

load_dotenv()

logger = get_logger("agent")  # use centralized logger

mode = os.environ.get("MODE", "local")
logger.info(f"Running in {mode} mode")

if mode == "local":
    transport = "stdio"
else:
    transport = "sse"

model = ChatOllama(model="qwen2.5:7b")
logger.info(f"Using model: {model.model}")

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
        },
        "brave": {
            "command": "python",
            "args": ["/Users/garyj/Code/mcpserver/src/servers/brave_server.py"],
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
        },
        "brave": {
            "command": "python",
            "url": os.environ.get("BRAVE_URL", "http://localhost:5002/mcp/sse"),
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
    # query = "What is the weather in San Francisco?"
    # query = "Who is Alex Karp?"
    response = asyncio.run(main(query))
    print(response)
