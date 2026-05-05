# MCP Server Boilerplate

A minimal, well-documented MCP (Model Context Protocol) server implementation designed to serve as a reusable baseline for building custom MCP servers.

## What is MCP?

The Model Context Protocol (MCP) is a standardized protocol that enables AI assistants to interact with external servers. MCP servers can provide:

- **Tools**: Functions that the AI can call to perform actions
- **Resources**: Static or dynamic data that the AI can read
- **Prompts**: Reusable prompt templates for consistent AI interactions

## Features

This boilerplate provides:

- **Minimal structure**: Clean baseline that can be easily extended
- **Extensive documentation**: Inline comments and separate documentation files
- **Architecture diagrams**: Mermaid diagrams showing component interactions
- **Scaling guide**: Best practices for growing your server
- **Type hints**: Full type annotations for better IDE support
- **Async/await**: Non-blocking I/O for concurrent operations

## Reusable Prompt Templates

Prompts are reusable prompt templates that allow you to define structured prompts with placeholders. They enable:

- **Consistency**: Standardized prompt formats across different AI interactions
- **Parameterization**: Dynamic content insertion through arguments
- **Reusability**: Define once, use multiple times with different inputs
- **Type safety**: Defined argument schemas with validation

A prompt template consists of:
- **Name**: Unique identifier for the prompt
- **Description**: What the prompt does
- **Arguments**: Optional parameters that can be filled in when using the prompt

Example use cases:
- Code review templates with configurable severity levels
- Documentation generation with customizable tone
- Analysis prompts with variable focus areas
- Report generation with different output formats

## Project Structure

```
windsurf-project-3/
├── mcp_server.py          # Main server implementation with extensive comments
├── pyproject.toml         # Project configuration for uv
├── ARCHITECTURE.md        # Architecture documentation with Mermaid diagrams
├── SCALING_GUIDE.md       # Scaling patterns and best practices
├── README.md              # This file
├── tools/                 # Placeholder for tool modules (create as needed)
├── resources/             # Placeholder for resource modules (create as needed)
├── prompts/               # Placeholder for prompt modules (create as needed)
└── utils/                 # Placeholder for utility modules (create as needed)
```

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management.

1. Install Python 3.10 or higher
2. Install uv (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
3. Install dependencies:
```bash
uv sync
```

**For SSE (remote HTTP) transport support:**
```bash
uv sync --extra sse
```

This installs FastAPI, uvicorn, and SSE-related dependencies for remote deployment.

## Transport Modes

This boilerplate supports two transport modes for MCP communication:

### stdio Mode (Default)
- **Use case**: Local development, CLI tools, desktop applications
- **How it works**: Server runs as a subprocess, communicates via stdin/stdout
- **Configuration**: Default mode, no configuration needed
- **Client setup**: Configure MCP client to run the server as a command

```bash
# Run in stdio mode (default)
uv run python mcp_server.py
```

### SSE Mode (Server-Sent Events)
- **Use case**: Web clients, remote deployment, production scenarios
- **How it works**: HTTP server with SSE for streaming responses
- **Configuration**: Set `MCP_TRANSPORT=sse` environment variable
- **Client setup**: Configure MCP client with HTTP endpoint URL

```bash
# Install SSE dependencies
uv sync --extra sse

# Run in SSE mode
MCP_TRANSPORT=sse uv run python mcp_server.py
```

**SSE Configuration:**
- `MCP_TRANSPORT=sse` - Enable SSE transport
- `MCP_HOST=0.0.0.0` - Host to bind to (default: 0.0.0.0)
- `MCP_PORT=8000` - Port to listen on (default: 8000)

**SSE Endpoints:**
- `GET /sse` - SSE endpoint for event streaming
- `POST /messages` - POST endpoint for client requests
- `GET /health` - Health check endpoint

## Quick Start

### 1. Add Your First Tool

Edit `mcp_server.py` and add a tool in the `list_tools()` function:

```python
@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="echo",
            description="Echo back the input text",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to echo"}
                },
                "required": ["text"]
            }
        )
    ]
```

### 2. Implement the Tool Handler

Add the tool logic in the `call_tool()` function:

```python
@app.call_tool()
async def call_tool(name: str, arguments: Any) -> str:
    if name == "echo":
        text = arguments.get("text", "")
        return f"Echo: {text}"
    raise ValueError(f"Unknown tool: {name}")
```

### 3. Add a Prompt (Optional)

Add a prompt in the `list_prompts()` function:

```python
@app.list_prompts()
async def list_prompts() -> list[Prompt]:
    return [
        Prompt(
            name="example_prompt",
            description="An example prompt template",
            arguments=[
                PromptArgument(
                    name="topic",
                    description="The topic to write about",
                    required=True
                )
            ]
        )
    ]
```

Then implement the handler in `get_prompt()`:

```python
@app.get_prompt()
async def get_prompt(name: str, arguments: dict[str, str] | None) -> str:
    if name == "example_prompt":
        topic = arguments.get("topic") if arguments else None
        if not topic:
            raise ValueError("Argument 'topic' is required")
        return f"Write a detailed explanation about {topic}."
    raise ValueError(f"Unknown prompt: {name}")
```

### 3. Run the Server

```bash
uv run python mcp_server.py
```

### 4. Configure Your MCP Client

**For stdio mode (local):**

Add this to your MCP client's configuration:

```json
{
  "mcpServers": {
    "your-server-name": {
      "command": "uv",
      "args": ["run", "python", "/path/to/mcp_server.py"]
    }
  }
}
```

**For SSE mode (remote):**

Add this to your MCP client's configuration:

```json
{
  "mcpServers": {
    "your-server-name": {
      "url": "http://localhost:8000/sse",
      "transport": "sse"
    }
  }
}
```

For production deployment, replace `http://localhost:8000` with your actual server URL.

## Documentation

- **ARCHITECTURE.md**: Detailed architecture documentation with Mermaid diagrams showing:
  - Python modules and their purposes
  - Component interactions
  - Request flows (tool invocation, resource reading, prompt retrieval)
  - Transport modes (stdio and SSE)
  - Design patterns used

- **SCALING_GUIDE.md**: Best practices for scaling your server:
  - Modularization patterns
  - State management strategies
  - Error handling patterns
  - Logging and monitoring
  - Configuration management
  - Testing strategies
  - Performance optimization
  - Security considerations
  - SSE deployment guidance

## Production Deployment

### SSE Mode Deployment

For production deployment using SSE transport:

1. **Install SSE dependencies:**
```bash
uv sync --extra sse
```

2. **Configure environment variables:**
```bash
export MCP_TRANSPORT=sse
export MCP_HOST=0.0.0.0
export MCP_PORT=8000
```

3. **Run with a production ASGI server:**
```bash
uv run uvicorn mcp_server:web_app --host 0.0.0.0 --port 8000 --workers 4
```

4. **Containerization (Docker):**
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync --extra sse
ENV MCP_TRANSPORT=sse
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000
CMD ["uv", "run", "uvicorn", "mcp_server:web_app", "--host", "0.0.0.0", "--port", "8000"]
```

5. **Health checks:**
- The server provides a `/health` endpoint for monitoring
- Returns server status and active session count
- Use for container orchestration (Kubernetes, Docker health checks)

### Security Considerations for Production

- **Authentication**: Add authentication middleware to FastAPI app
- **CORS**: Configure CORS for web client access
- **Rate limiting**: Implement rate limiting to prevent abuse
- **TLS**: Use reverse proxy (nginx, traefik) for HTTPS termination
- **Secrets**: Use environment variables or secret management for API keys

See SCALING_GUIDE.md for detailed security patterns.

## Code Structure

The main server file (`mcp_server.py`) is organized into sections:

1. **Server Initialization**: Create the MCP server instance
2. **Tool Registration**: Define available tools
3. **Tool Handlers**: Implement tool execution logic
4. **Resource Registration**: Define available resources
5. **Resource Handlers**: Implement resource reading logic
6. **Entry Point**: Start the server with stdio communication

Each section includes extensive inline comments explaining the purpose and usage of each component.

## Extension Points

### Adding Tools

1. Define the tool in `list_tools()` with its schema
2. Implement the handler in `call_tool()`
3. For larger projects, move to separate module in `tools/` directory

### Adding Prompts

1. Define the prompt in `list_prompts()` with its arguments
2. Implement the handler in `get_prompt()`
3. For larger projects, move to separate module in `prompts/` directory

### Adding Resources

1. Define the resource in `list_resources()` with its metadata
2. Implement the handler in `read_resource()`
3. For larger projects, move to separate module in `resources/` directory

### Adding Utilities

Extract shared code into the `utils/` directory:
- Validation functions
- Logging helpers
- Configuration management
- Error handling utilities

## Using as a Baseline

This boilerplate is designed to be copied and modified for new projects:

1. Copy the entire project directory
2. Rename the project in `pyproject.toml`
3. Update the server name in `mcp_server.py`
4. Add your tools, resources, and prompts
5. Customize documentation as needed

## Python Modules Used

- **`mcp.server.Server`**: Main MCP server class
- **`mcp.types.Tool`**: Tool type definition
- **`mcp.types.Resource`**: Resource type definition
- **`mcp.types.Prompt`**: Prompt type definition
- **`mcp.types.PromptArgument`**: Prompt argument type definition
- **`mcp.server.stdio`**: Stdio communication streams
- **`asyncio`**: Async/await for concurrent operations
- **`typing`**: Type hints for code clarity

See `ARCHITECTURE.md` for detailed explanations of each module.

## Development

### Running Tests

```bash
# Run with pytest (add tests first)
uv run pytest
```

### Code Style

This project uses Python type hints and follows PEP 8 conventions. Consider using:
- `ruff` for linting
- `mypy` for type checking

### Adding Dependencies

```bash
uv add <package-name>
```

## Troubleshooting

- **Import error**: Run `uv sync` to install dependencies
- **Server not responding**: Check MCP client configuration
- **Type errors**: Ensure Python 3.10+ is installed
- **uv command not found**: Install uv from https://github.com/astral-sh/uv

## Resources

- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [uv Documentation](https://github.com/astral-sh/uv)

## License

This boilerplate is provided as-is for educational and development purposes. Feel free to use and modify it for your projects.
