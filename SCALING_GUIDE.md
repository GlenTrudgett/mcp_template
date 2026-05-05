# MCP Server Scaling Guide

This guide provides general patterns and best practices for scaling your MCP server from a minimal boilerplate to a production-ready implementation.

## Transport Mode Selection

This boilerplate supports two transport modes:
- **stdio (default)**: Local communication via stdin/stdout for CLI tools
- **SSE**: Remote HTTP/SSE communication for web clients and production

Set the transport mode via the `MCP_TRANSPORT` environment variable:
```bash
MCP_TRANSPORT=stdio   # Local mode (default)
MCP_TRANSPORT=sse     # Remote HTTP/SSE mode
```

**When to use each:**
- Use **stdio** for local development, desktop applications, and CLI tools
- Use **SSE** for web clients, remote deployment, and production scenarios

## Modularization

### Separate Tool Modules

As your server grows, separate tools into individual modules for better organization:

```python
# tools/example_tool.py
from mcp.types import Tool

def get_tool_definition() -> Tool:
    """Return the tool definition."""
    return Tool(
        name="example_tool",
        description="An example tool",
        inputSchema={"type": "object", "properties": {}, "required": []}
    )

async def execute_tool(arguments: dict) -> str:
    """Execute the tool logic."""
    return "Tool result"
```

```python
# mcp_server.py
from tools import example_tool

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [example_tool.get_tool_definition()]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> str:
    if name == "example_tool":
        return await example_tool.execute_tool(arguments)
    # ... other tools
```

### Separate Resource Modules

Apply the same pattern to resources:

```python
# resources/example_resource.py
from mcp.types import Resource

def get_resource_definition() -> Resource:
    """Return the resource definition."""
    return Resource(
        uri="server://example",
        name="Example Resource",
        description="An example resource",
        mimeType="text/plain"
    )

async def read_resource() -> str:
    """Read or generate the resource content."""
    return "Resource content"
```

### Separate Prompt Modules

Apply the same pattern to prompts:

```python
# prompts/example_prompt.py
from mcp.types import Prompt, PromptArgument

def get_prompt_definition() -> Prompt:
    """Return the prompt definition."""
    return Prompt(
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

async def generate_prompt(arguments: dict[str, str] | None) -> str:
    """Generate the prompt with given arguments."""
    if not arguments:
        raise ValueError("Arguments are required")
    topic = arguments.get("topic")
    if not topic:
        raise ValueError("Argument 'topic' is required")
    return f"Write a detailed explanation about {topic}."
```

### Utility Modules

Extract shared utilities:

```python
# utils/validation.py
def validate_required_fields(data: dict, required: list[str]) -> None:
    """Validate that required fields are present."""
    missing = [field for field in required if field not in data]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

# utils/logging.py
import logging

logger = logging.getLogger(__name__)

def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the server."""
    logging.basicConfig(level=level)
```

## State Management

### Session State

For per-session state (e.g., conversation context):

```python
class SessionState:
    """Manages state for a single session."""
    
    def __init__(self):
        self.context = {}
        self.history = []
    
    def update_context(self, key: str, value: Any) -> None:
        """Update a context value."""
        self.context[key] = value
    
    def add_to_history(self, entry: str) -> None:
        """Add an entry to the history."""
        self.history.append(entry)

# Usage in handlers
session_state = SessionState()
```

### Persistent Storage

For state that persists across sessions:

```python
import json
from pathlib import Path

class PersistentStorage:
    """Manages persistent storage using JSON files."""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.data = self._load()
    
    def _load(self) -> dict:
        """Load data from storage."""
        if self.storage_path.exists():
            return json.loads(self.storage_path.read_text())
        return {}
    
    def save(self) -> None:
        """Save data to storage."""
        self.storage_path.write_text(json.dumps(self.data))
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from storage."""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in storage."""
        self.data[key] = value
        self.save()
```

### Database Integration

For more complex persistence needs:

```python
import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db_connection(db_path: str):
    """Context manager for database connections."""
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()

# Usage
with get_db_connection("server.db") as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM data")
    results = cursor.fetchall()
```

## Error Handling Patterns

### Custom Exceptions

Define domain-specific exceptions:

```python
class MCPServerError(Exception):
    """Base exception for MCP server errors."""
    pass

class ToolExecutionError(MCPServerError):
    """Raised when tool execution fails."""
    def __init__(self, tool_name: str, reason: str):
        self.tool_name = tool_name
        self.reason = reason
        super().__init__(f"Tool '{tool_name}' failed: {reason}")

class ResourceNotFoundError(MCPServerError):
    """Raised when a resource is not found."""
    def __init__(self, uri: str):
        self.uri = uri
        super().__init__(f"Resource not found: {uri}")
```

### Error Recovery

Implement graceful error handling:

```python
@app.call_tool()
async def call_tool(name: str, arguments: Any) -> str:
    """Execute a tool with error recovery."""
    try:
        if name == "example_tool":
            return await execute_example_tool(arguments)
        # ... other tools
    except ValidationError as e:
        logger.warning(f"Validation error in {name}: {e}")
        return f"Error: Invalid arguments - {str(e)}"
    except ToolExecutionError as e:
        logger.error(f"Tool execution error: {e}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.exception(f"Unexpected error in {name}")
        return f"Error: An unexpected error occurred"
```

### Input Validation

Validate inputs before processing:

```python
def validate_tool_arguments(schema: dict, arguments: dict) -> None:
    """Validate arguments against a JSON schema."""
    # Implement JSON schema validation
    # Use jsonschema library for robust validation
    import jsonschema
    jsonschema.validate(arguments, schema)
```

## Logging and Monitoring

### Structured Logging

Use structured logging for better observability:

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    """Format log messages as JSON."""
    
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        return json.dumps(log_data)

# Configure logging
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

### Metrics Collection

Track important metrics:

```python
from collections import defaultdict
from time import time

class MetricsCollector:
    """Collect and track server metrics."""
    
    def __init__(self):
        self.tool_calls = defaultdict(int)
        self.resource_reads = defaultdict(int)
        self.prompt_generations = defaultdict(int)
        self.errors = defaultdict(int)
        self.latencies = defaultdict(list)
    
    def record_tool_call(self, tool_name: str, duration: float) -> None:
        """Record a tool call."""
        self.tool_calls[tool_name] += 1
        self.latencies[tool_name].append(duration)
    
    def record_resource_read(self, uri: str) -> None:
        """Record a resource read."""
        self.resource_reads[uri] += 1
    
    def record_prompt_generation(self, prompt_name: str) -> None:
        """Record a prompt generation."""
        self.prompt_generations[prompt_name] += 1
    
    def record_error(self, error_type: str) -> None:
        """Record an error."""
        self.errors[error_type] += 1
    
    def get_summary(self) -> dict:
        """Get a summary of metrics."""
        return {
            "tool_calls": dict(self.tool_calls),
            "resource_reads": dict(self.resource_reads),
            "prompt_generations": dict(self.prompt_generations),
            "errors": dict(self.errors),
            "avg_latencies": {
                k: sum(v) / len(v) for k, v in self.latencies.items()
            }
        }

# Usage
metrics = MetricsCollector()

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> str:
    start = time()
    try:
        result = await execute_tool(name, arguments)
        metrics.record_tool_call(name, time() - start)
        return result
    except Exception as e:
        metrics.record_error(type(e).__name__)
        raise
```

## Configuration Management

### Environment Variables

Use environment variables for configuration:

```python
import os
from typing import Optional

class Config:
    """Server configuration from environment variables."""
    
    def __init__(self):
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.storage_path: str = os.getenv("STORAGE_PATH", "./storage")
        self.max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
        self.timeout: float = float(os.getenv("TIMEOUT", "30.0"))
    
    def validate(self) -> None:
        """Validate configuration values."""
        if self.max_retries < 0:
            raise ValueError("MAX_RETRIES must be non-negative")
        if self.timeout <= 0:
            raise ValueError("TIMEOUT must be positive")

config = Config()
config.validate()
```

### Configuration Files

For more complex configuration:

```python
import yaml
from pathlib import Path

class Config:
    """Server configuration from YAML file."""
    
    def __init__(self, config_path: Path):
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: Path) -> dict:
        """Load configuration from YAML file."""
        with open(config_path) as f:
            return yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        keys = key.split(".")
        value = self.config
        for k in keys:
            value = value.get(k, {})
        return value if value != {} else default
```

## Testing Strategies

### Unit Testing

Test individual components:

```python
import pytest
from tools.example_tool import execute_tool

@pytest.mark.asyncio
async def test_example_tool():
    """Test the example tool."""
    result = await execute_tool({"param": "test"})
    assert result == "Expected result"

@pytest.mark.asyncio
async def test_example_tool_validation():
    """Test tool validation."""
    with pytest.raises(ValueError):
        await execute_tool({})
```

### Integration Testing

Test the full server:

```python
import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

@pytest.mark.asyncio
async def test_server_integration():
    """Test the full MCP server integration."""
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"]
    )
    
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # Test tool listing
            tools = await session.list_tools()
            assert len(tools.tools) > 0
            
            # Test tool invocation
            result = await session.call_tool("example_tool", {})
            assert result.content[0].text
            
            # Test prompt listing
            prompts = await session.list_prompts()
            assert len(prompts.prompts) > 0
            
            # Test prompt retrieval
            prompt = await session.get_prompt("example_prompt", {"topic": "test"})
            assert prompt.content[0].text
```

### Mock Testing

Mock external dependencies:

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_tool_with_mock():
    """Test tool with mocked dependencies."""
    with patch("tools.example_tool.external_api_call", new_callable=AsyncMock) as mock:
        mock.return_value = "mocked result"
        result = await execute_tool({})
        assert result == "mocked result"
```

## Performance Optimization

### Caching

Cache expensive operations:

```python
from functools import lru_cache
from datetime import datetime, timedelta

class TTLCache:
    """Cache with time-to-live expiration."""
    
    def __init__(self, ttl: timedelta):
        self.ttl = ttl
        self.cache = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache if not expired."""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                return value
            del self.cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in cache."""
        self.cache[key] = (value, datetime.now())

# Usage
cache = TTLCache(timedelta(hours=1))

async def get_expensive_data(key: str) -> str:
    """Get data with caching."""
    cached = cache.get(key)
    if cached:
        return cached
    result = await fetch_data(key)
    cache.set(key, result)
    return result
```

### Connection Pooling

Pool database or API connections:

```python
import aiohttp
from contextlib import asynccontextmanager

class ConnectionPool:
    """Manages a pool of HTTP connections."""
    
    def __init__(self, max_connections: int = 10):
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=max_connections)
        )
    
    async def close(self) -> None:
        """Close the connection pool."""
        await self.session.close()
    
    @asynccontextmanager
    async def get(self, url: str):
        """Get a connection for a request."""
        async with self.session.get(url) as response:
            yield response

# Usage
pool = ConnectionPool()

async def fetch_data(url: str) -> str:
    """Fetch data using connection pool."""
    async with pool.get(url) as response:
        return await response.text()
```

## Security Considerations

### SSE-Specific Security

When using SSE transport for remote deployment, implement these security measures:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

web_app = FastAPI()

# Configure CORS for web client access
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Restrict to specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Add authentication middleware
from fastapi import Header, HTTPException

async def verify_auth(authorization: str = Header(...)):
    """Verify authentication token."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization[7:]
    # Validate token against your auth system
    if not validate_token(token):
        raise HTTPException(status_code=403, detail="Invalid token")
    return token

# Protect SSE endpoint with auth
@web_app.get("/sse", dependencies=[Depends(verify_auth)])
async def sse_endpoint():
    # ... SSE implementation
    pass
```

### SSE Production Deployment

For production deployment with SSE transport:

**1. Containerization (Docker):**

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync --extra sse
ENV MCP_TRANSPORT=sse
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "mcp_server:web_app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**2. Production Server Configuration:**

```bash
# Run with uvicorn for production
uv run uvicorn mcp_server:web_app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info \
    --access-log \
    --timeout-keep-alive 75
```

**3. Environment Variables:**

```bash
export MCP_TRANSPORT=sse
export MCP_HOST=0.0.0.0
export MCP_PORT=8000
export LOG_LEVEL=info
```

**4. Health Checks:**

The `/health` endpoint provides:
- Server status (healthy/unhealthy)
- Transport mode
- Active session count

Use for:
- Kubernetes liveness/readiness probes
- Docker health checks
- Load balancer health checks

**5. TLS/HTTPS:**

Use a reverse proxy for TLS termination:
- Nginx, Traefik, or Caddy
- Configure proxy to forward to http://localhost:8000
- Handle SSL certificates at the proxy layer

### Input Sanitization

Sanitize all user inputs:

```python
import html

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    return html.escape(text)

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> str:
    """Execute tool with input sanitization."""
    if isinstance(arguments, dict):
        for key, value in arguments.items():
            if isinstance(value, str):
                arguments[key] = sanitize_input(value)
    # ... rest of implementation
```

### Rate Limiting

Implement rate limiting to prevent abuse:

```python
from collections import defaultdict
from time import time

class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed."""
        now = time()
        # Remove old requests outside the window
        self.requests[identifier] = [
            t for t in self.requests[identifier]
            if now - t < self.window_seconds
        ]
        # Check if under limit
        if len(self.requests[identifier]) < self.max_requests:
            self.requests[identifier].append(now)
            return True
        return False

# Usage
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> str:
    """Execute tool with rate limiting."""
    client_id = arguments.get("client_id", "default")
    if not rate_limiter.is_allowed(client_id):
        raise ValueError("Rate limit exceeded")
    # ... rest of implementation
```

### Authentication

Add authentication if needed:

```python
import jwt
from datetime import datetime, timedelta

class AuthManager:
    """Manages authentication using JWT tokens."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def generate_token(self, user_id: str) -> str:
        """Generate a JWT token."""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def validate_token(self, token: str) -> Optional[str]:
        """Validate a JWT token and return user_id."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload.get("user_id")
        except jwt.InvalidTokenError:
            return None

# Usage
auth = AuthManager(secret_key="your-secret-key")

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> str:
    """Execute tool with authentication."""
    token = arguments.get("token")
    user_id = auth.validate_token(token)
    if not user_id:
        raise ValueError("Invalid or expired token")
    # ... rest of implementation
```

## Summary

When scaling your MCP server, focus on:

1. **Modularization**: Separate concerns into distinct modules (tools, resources, prompts)
2. **State Management**: Choose appropriate persistence strategy
3. **Error Handling**: Implement graceful error recovery
4. **Logging/Monitoring**: Add observability for production
5. **Configuration**: Use environment variables or config files
6. **Testing**: Write comprehensive tests
7. **Performance**: Cache expensive operations, pool connections
8. **Security**: Sanitize inputs, rate limit, authenticate
9. **Transport Selection**: Choose stdio for local, SSE for remote deployment
10. **Production Deployment**: Use uvicorn with workers, health checks, and TLS

Apply these patterns incrementally as your server grows in complexity.
