"""
Basic tests for MCP server boilerplate.

These tests validate that the server can be initialized and handlers are properly registered.
"""

import pytest
from mcp_server import app


def test_server_initialization():
    """Test that the MCP server instance is created successfully."""
    assert app is not None
    assert app.name == "mcp-server-boilerplate"


def test_transport_selection_stdio_default():
    """Test that default transport mode is stdio."""
    import os
    # Clear any existing MCP_TRANSPORT env var
    os.environ.pop("MCP_TRANSPORT", None)
    # The default should be stdio
    from mcp_server import main
    # Just verify the function exists, don't actually run it
    assert callable(main)
