# MCP Server

A simple MCP (Model Context Protocol) server project implementing two services—**weather** and **math**—using FastAPI and Docker. This project deploys the MCP servers inside Docker containers, making them remotely accessible via a FastAPI app. Whether you are deploying infrastructure locally or in the cloud, these MCP servers can be called by any external application (for example, Claude) without exposing your host machine. For added security, dockerizing the MCP servers is a best practice.

In this example, the agent uses a local model Ollama deployed on port **11434** to process queries.

## Features

- **Weather Server:** Provides weather lookup tools (`get_weather`, `get_coordinates`).
- **Math Server:** Provides simple math tools (`add`, `multiply`).
- **FastAPI Integration:** Both MCP servers (implemented with FastMCP) are embedded inside a FastAPI application.
  - The FastAPI app specifies the host and port via uvicorn.
  - Routing is managed by the `register_mcp_router` function (located in `src/models/utils.py`), which mounts the necessary SSE endpoints.
- **Remote Accessibility:** Deployed via Docker Compose, the MCP servers’ endpoints can be accessed remotely by any client or external service (like Claude) without requiring local installation.
- **Local and Remote Infrastructure:** This app is built for users deploying local or remote infrastructure.
- **Local Model Example:** An example agent is provided that uses a locally deployed model Ollama running on port **11434**.
- **MCP Inspector:** For testing and debugging, [MCP Inspector](https://github.com/modelcontextprotocol/inspector) can be launched via:
  ```sh
  mcp dev ./src/servers/math_server.py
  ```
  This tool provides a nice GUI to test and interact with your MCP servers.

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
   # (Optional) An API key for additional services:
   SMITHERY_API_KEY=your-api-key
   ```

## Running via Docker Compose

The MCP servers are deployed in Docker containers that embed FastMCP into a FastAPI app. This configuration specifies the host and port and manages routing using the `register_mcp_router` function from `src/models/utils.py`.

1. **Build and bring up the services:**

   ```sh
   docker-compose up --build
   ```

2. **Check the logs:**

   - The Math server logs will show it listening on port `5001`.
   - The Weather server logs will show it listening on port `5000`.

3. **Test the endpoints:**

   - Weather SSE endpoint: [http://localhost:5000/mcp/sse](http://localhost:5000/mcp/sse)
   - Math SSE endpoint: [http://localhost:5001/mcp/sse](http://localhost:5001/mcp/sse)

   These endpoints will be accessible remotely if your network configuration permits.

## Running the Agent

An example agent is provided to connect to and query the MCP servers. The agent reads configuration from the `.env` file and uses the provided endpoints. In this example, the agent also uses a local model Ollama that is deployed on port **11434**.

To run the agent locally:

```sh
python agent.py
```

The agent will log its process, connect to the MCP servers, send a query, and display the response.

## Testing with MCP Inspector

For a GUI-based testing and debugging experience, you can use MCP Inspector to launch a graphical interface for your MCP servers. For example, you can launch MCP Inspector for the math server by running:

```sh
mcp dev ./src/servers/math_server.py
```

This tool is great for quickly testing and interacting with your MCP servers without needing to write custom client code.

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
    │   └── utils.py      # Contains the register_mcp_router function to mount SSE endpoints
    └── servers/
        ├── math_server.py
        └── weather_server.py
```

## Logging

Each module uses a centralized logging format (timestamp, log level, module name). This assists in tracing requests, debugging, and monitoring system behavior.

## Security and Remote Deployment

By dockerizing the MCP servers, you isolate your core services from direct host access, reducing security risks. External applications (such as Claude) can communicate with these servers via defined REST/SSE endpoints without needing to run the services on your local machine. This setup is ideal for both remote infrastructure deployment and local testing.

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