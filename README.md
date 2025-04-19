# MCP Server

A simple MCP (Model Context Protocol) server project implementing two services—**weather** and **math**—using FastAPI and Docker. This project deploys the MCP servers inside Docker containers, making them remotely accessible via a FastAPI app. An example agent (agent.py) is provided to query these servers.

## Features

- **Weather Server:** Provides weather lookup tools (get_weather, get_coordinates).
- **Math Server:** Provides simple math tools (add, multiply).
- **FastAPI Integration:** Both MCP servers (implemented with FastMCP) are embedded inside a FastAPI application.  
  - The FastAPI app specifies the host and port via uvicorn.  
  - Routing is managed by the `register_mcp_router` function (located in `src/models/utils.py`), which mounts the necessary SSE endpoints.
- **Remote Accessibility:** Deployed via Docker Compose, the servers’ endpoints can be accessed remotely (provided network and firewall settings allow it).
- Supports both **local** mode (subprocess via stdio) for development and **production** mode (SSE over HTTP) for deployment.
- Centralized logging for clear debugging insights.
- An example agent that connects to and queries the deployed servers.

## Requirements

- Python 3.13
- [Poetry](https://python-poetry.org/)
- Docker and Docker Compose

## Installation

1. **Clone the repository:**

   ```sh
   git clone https://github.com/yourusername/mcpserver.git
   cd mcpserver
   ```

2. **Install dependencies using Poetry:**

   ```sh
   poetry install
   ```

3. **Create a `.env` file** at the root with the following example values:

   ```properties
   MATH_URL=http://localhost:5001/mcp/sse
   WEATHER_URL=http://localhost:5000/mcp/sse
   TRANSPORT=sse
   MODE=prod
   PORT_MATH_SERVER=5001
   PORT_WEATHER_SERVER=5000
   ```

## Running via Docker Compose

The MCP servers are deployed in Docker containers that embed FastMCP into a FastAPI app. This configuration specifies the host and port and manages routing using the `register_mcp_router` function from `src/models/utils.py`.

1. **Build and bring up the services:**

   ```sh
   docker-compose up --build
   ```

2. **Check the logs:**

   - The math server logs will show it listening on port `5001`.
   - The weather server logs will show it listening on port `5000`.

3. **Test the endpoints:**

   - Weather SSE endpoint: [http://localhost:5000/mcp/sse]
   - Math SSE endpoint: [http://localhost:5001/mcp/sse]

   These endpoints will be accessible remotely if your network configuration permits.

## Running the Agent

An example agent is provided to connect to and query the MCP servers. The agent reads configuration from the `.env` file and uses the provided endpoints.

To run the agent locally:

```sh
poetry run python agent.py
```

The agent will log its process, connect to the MCP servers, send a query, and display the response.

## Project Structure

```
mcpserver/
├── .env
├── Dockerfile.math
├── Dockerfile.weather
├── pyproject.toml
├── poetry.lock
├── docker-compose.yml
├── README.md
└── src/
    ├── agent.py
    ├── models/
    │   └── utils.py
    └── servers/
        ├── math_server.py
        └── weather_server.py
```

## Logging

Each module uses a centralized logging format (timestamp, log level, module name). Logs help in tracing requests, debugging, and monitoring the system behavior.

## Publishing on GitHub

1. **Initialize Git (if not already initialized):**

   ```sh
   git init
   ```

2. **Add files and commit:**

   ```sh
   git add .
   git commit -m "Initial commit of MCP server project"
   ```

3. **Create a GitHub repository** (e.g., `mcpserver`) and push:

   ```sh
   git remote add origin https://github.com/yourusername/mcpserver.git
   git branch -M main
   git push -u origin main
   ```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements.

## License

This project is licensed under the [MIT License](LICENSE).