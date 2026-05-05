#!/usr/bin/env python3
"""
MCP Server Boilerplate - Minimal Reusable Baseline

This is a minimal, well-documented MCP (Model Context Protocol) server implementation
designed to serve as a baseline for future projects. It includes extensive inline
comments explaining each component and can be easily extended with custom tools
and resources.

The MCP protocol allows AI assistants to interact with external servers through:
- Tools: Functions that the AI can call to perform actions
- Resources: Static or dynamic data that the AI can read
- Prompts: Reusable prompt templates

Transport Modes:
- stdio (default): Local communication via stdin/stdout
- sse: Remote HTTP/SSE communication via FastAPI

Set MCP_TRANSPORT environment variable to select mode:
    MCP_TRANSPORT=stdio  # Default - local mode
    MCP_TRANSPORT=sse    # Remote HTTP/SSE mode
"""

import asyncio
import os
from typing import Any

# MCP server imports
from mcp.server import Server
from mcp.types import Tool, Resource, Prompt, PromptArgument  # noqa: F401


# ============================================================================
# SERVER INITIALIZATION
# ============================================================================

# Create the MCP server instance with a unique identifier
# This identifier is used by MCP clients to distinguish between different servers
app = Server("mcp-server-boilerplate")


# ============================================================================
# TOOL REGISTRATION AND HANDLERS
# ============================================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    List all available tools provided by this server.
    
    This function is called by MCP clients to discover what tools are available.
    Each tool must have:
    - name: Unique identifier for the tool
    - description: Human-readable description of what the tool does
    - inputSchema: JSON Schema defining the expected input parameters
    
    Returns:
        list[Tool]: A list of Tool objects describing available tools
    """
    # TODO: Add your tools here
    # Example:
    # return [
    #     Tool(
    #         name="example_tool",
    #         description="Description of what this tool does",
    #         inputSchema={
    #             "type": "object",
    #             "properties": {
    #                 "param": {
    #                     "type": "string",
    #                     "description": "Parameter description"
    #                 }
    #             },
    #             "required": ["param"]
    #         }
    #     )
    # ]
    return []


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> str:
    """
    Execute a tool with the given name and arguments.
    
    This function is called when an MCP client invokes a tool.
    The function must:
    1. Match the tool name to a handler
    2. Validate the arguments (optional but recommended)
    3. Execute the tool logic
    4. Return the result as a string
    
    Args:
        name: The name of the tool to execute
        arguments: The arguments passed to the tool (typically a dict)
    
    Returns:
        str: The result of the tool execution
    
    Raises:
        ValueError: If the tool name is unknown or arguments are invalid
    """
    # TODO: Implement your tool handlers here
    # Example pattern:
    # if name == "example_tool":
    #     param = arguments.get("param")
    #     if not param:
    #         raise ValueError("Parameter 'param' is required")
    #     # Your tool logic here
    #     return f"Result: {param}"
    
    raise ValueError(f"Unknown tool: {name}")


# ============================================================================
# RESOURCE REGISTRATION AND HANDLERS
# ============================================================================

@app.list_resources()
async def list_resources() -> list[Resource]:
    """
    List all available resources provided by this server.

    This function is called by MCP clients to discover what resources are available.
    Each resource must have:
    - uri: Unique identifier for the resource (e.g., "server://info")
    - name: Human-readable name for the resource
    - description: Description of what the resource contains
    - mimeType: MIME type indicating the resource format (e.g., "text/plain", "application/json")

    Returns:
        list[Resource]: A list of Resource objects describing available resources
    """
    return [
        Resource(
            uri="server://status",
            name="Server Status",
            description="Current server metrics including uptime, memory usage, and CPU load",
            mimeType="application/json"
        ),
        Resource(
            uri="server://info",
            name="Server Info",
            description="Server configuration and version information",
            mimeType="application/json"
        )
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """
    Read a resource by its URI.

    This function is called when an MCP client requests to read a resource.
    The function must:
    1. Match the URI to a resource handler
    2. Retrieve or generate the resource content
    3. Return the content as a string

    Args:
        uri: The URI of the resource to read

    Returns:
        str: The content of the resource

    Raises:
        ValueError: If the URI is unknown

    Note: For production servers with many resources, consider using a registry pattern
    instead of if/elif chains. See SCALING_GUIDE.md for scalable alternatives.
    """
    import json
    import sys
    from datetime import datetime

    if uri == "server://status":
        import psutil

        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": psutil.boot_time(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total_bytes": psutil.virtual_memory().total,
                "available_bytes": psutil.virtual_memory().available,
                "percent_used": psutil.virtual_memory().percent
            },
            "disk": {
                "total_bytes": psutil.disk_usage('/').total,
                "used_bytes": psutil.disk_usage('/').used,
                "percent_used": psutil.disk_usage('/').percent
            }
        }
        return json.dumps(status, indent=2)

    elif uri == "server://info":
        info = {
            "server_name": "mcp-server-boilerplate",
            "version": "0.1.0",
            "transport_mode": os.getenv("MCP_TRANSPORT", "stdio"),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }
        return json.dumps(info, indent=2)

    raise ValueError(f"Unknown resource URI: {uri}")


# ============================================================================
# PROMPT REGISTRATION AND HANDLERS
# ============================================================================

@app.list_prompts()
async def list_prompts() -> list[Prompt]:
    """
    List all available prompts provided by this server.

    This function is called by MCP clients to discover what prompts are available.
    Each prompt must have:
    - name: Unique identifier for the prompt
    - description: Human-readable description of what the prompt does
    - arguments (optional): List of PromptArgument objects defining template variables

    Each PromptArgument must have:
    - name: Name of the argument/variable in the template
    - description: Description of what the argument represents
    - required (optional): Whether the argument is required (default: false)

    Returns:
        list[Prompt]: A list of Prompt objects describing available prompts
    """
    return [
        Prompt(
            name="code_review",
            description="Guides AI assistants to perform thorough code reviews focusing on security, performance, and best practices",
            arguments=[
                PromptArgument(
                    name="language",
                    description="Programming language of the code being reviewed (e.g., python, javascript, go)",
                    required=True
                ),
                PromptArgument(
                    name="focus_area",
                    description="Specific area to focus on (e.g., security, performance, readability, all)",
                    required=False
                )
            ]
        )
    ]


@app.get_prompt()
async def get_prompt(name: str, arguments: dict[str, str] | None) -> str:
    """
    Get a prompt template with arguments filled in.

    This function is called when an MCP client requests a prompt.
    The function must:
    1. Match the prompt name to a handler
    2. Validate the provided arguments against the prompt's requirements
    3. Fill in the template with the arguments
    4. Return the completed prompt as a string

    Args:
        name: The name of the prompt to retrieve
        arguments: Optional dictionary of argument names to values

    Returns:
        str: The completed prompt template with arguments filled in

    Raises:
        ValueError: If the prompt name is unknown or arguments are invalid/missing
    """
    if name == "code_review":
        language = arguments.get("language") if arguments else None
        if not language:
            raise ValueError("Argument 'language' is required")
        focus_area = arguments.get("focus_area", "all") if arguments else "all"

        prompt = f"""You are performing a code review for {language} code.
Focus area: {focus_area}

Please review the code with attention to:
"""

        if focus_area in ["all", "security"]:
            prompt += "- Security vulnerabilities (SQL injection, XSS, authentication issues)\n"
        if focus_area in ["all", "performance"]:
            prompt += "- Performance bottlenecks and optimization opportunities\n"
        if focus_area in ["all", "readability"]:
            prompt += "- Code readability, naming conventions, and documentation\n"

        prompt += """- Error handling and edge cases
- Adherence to best practices
- Potential bugs or logic errors

Provide specific, actionable feedback with code examples where appropriate."""

        return prompt

    raise ValueError(f"Unknown prompt: {name}")


# ============================================================================
# SERVER ENTRY POINT
# ============================================================================

async def main():
    """
    Main entry point for the MCP server.

    This function supports two transport modes:
    1. stdio (default): Local communication via stdin/stdout
    2. sse: Remote HTTP/SSE communication via FastAPI

    Transport mode is selected via MCP_TRANSPORT environment variable.
    Default is stdio for local development and CLI tools.
    Use sse for web clients, remote deployment, and production scenarios.
    """
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()

    if transport == "sse":
        # SSE Mode: Remote HTTP/SSE transport
        # Requires FastAPI and related dependencies (install with: uv sync --extra sse)
        try:
            from fastapi import FastAPI
            import uvicorn
        except ImportError as e:
            raise ImportError(
                "SSE transport requires FastAPI dependencies. "
                "Install with: uv sync --extra sse"
            ) from e

        # Create FastAPI application
        web_app = FastAPI(title="MCP Server", version="0.1.0")

        # Track active SSE sessions for cleanup
        active_sessions = {}

        @web_app.get("/health")
        async def health_check():
            """
            Health check endpoint for monitoring and container orchestration.
            Returns server status and active session count.
            """
            return {
                "status": "healthy",
                "transport": "sse",
                "active_sessions": len(active_sessions)
            }

        @web_app.get("/sse")
        async def sse_endpoint():
            """
            SSE endpoint for server-to-client event streaming.
            Clients connect here to receive server responses and notifications.
            """
            from mcp.server.sse import SseServerTransport

            # Create SSE transport
            transport = SseServerTransport("/messages")

            # Create a new server instance for this session
            server = Server("mcp-server-boilerplate")
            server._transport_type = "sse"

            # Register handlers (same as stdio mode)
            # Note: In production, you'd want to register these once and reuse
            # For simplicity, we're registering per-session here
            # TODO: Extract handler registration to a shared function

            # Connect the server to the SSE transport
            async with transport.connect() as (read_stream, write_stream):
                await server.run(
                    read_stream,
                    write_stream,
                    server.create_initialization_options()
                )

        @web_app.post("/messages")
        async def messages_endpoint(request: dict):
            """
            POST endpoint for client-to-server JSON-RPC messages.
            Clients send requests here when using SSE transport.
            """
            # In a full implementation, this would route messages to the appropriate session
            # For now, return a placeholder response
            return {"error": "Session-based message routing not implemented in this minimal version"}

        # Get configuration from environment variables
        host = os.getenv("MCP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_PORT", "8000"))

        # Run the FastAPI server with uvicorn
        print(f"MCP server running in SSE mode on http://{host}:{port}")
        print(f"  SSE endpoint: http://{host}:{port}/sse")
        print(f"  Health check: http://{host}:{port}/health")

        uvicorn.run(web_app, host=host, port=port)

    else:
        # stdio Mode (default): Local communication via stdin/stdout
        # This is the standard way MCP servers integrate with MCP clients
        # The server runs as a subprocess and communicates via stdin/stdout
        from mcp.server.stdio import stdio_server

        print("MCP server running in stdio mode")

        # Create stdio server for communication
        async with stdio_server() as (read_stream, write_stream):
            # Run the MCP server with the streams
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
