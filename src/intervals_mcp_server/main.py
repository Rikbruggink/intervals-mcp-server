"""
Intervals.icu MCP Server

This module implements a Model Context Protocol (MCP) server for connecting
Claude with the Intervals.icu API. It provides tools for retrieving and managing
athlete data, including activities, events, workouts, and wellness metrics.

Key features:
- Activity retrieval and detailed analysis
- Event management (races, workouts, calendar items)
- Wellness data tracking and visualization
- Error handling with user-friendly messages
- Configurable parameters with environment variable support

The server follows MCP specifications and uses the Python MCP SDK.

The server is designed to be run as a standalone script.
"""

from server import mcp

# Import tools so they get registered via decorators
import tools.activities
import tools.events
import tools.welness


# Entry point to run the server
if __name__ == "__main__":
    mcp.run()