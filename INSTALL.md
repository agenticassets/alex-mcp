# OpenAlex MCP Server Installation Guide

This guide provides instructions for installing and running the OpenAlex MCP server.

## Prerequisites

- Python 3.10 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/drAbreu/alex-mcp.git
   cd alex-mcp
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```

3. Activate the virtual environment:
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install the package in development mode:
   ```bash
   pip install -e .
   ```

## Running the Server

### Option 1: Using the run script

The easiest way to run the server is to use the provided run script:

```bash
./run_alex_mcp.sh
```

This script activates the virtual environment and runs the server.

### Option 2: Manual execution

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Run the server:
   ```bash
   python run_server.py
   ```

## Using with Claude Desktop

To use this MCP server with Claude Desktop, add the following configuration:

```json
{
  "mcpServers": {
    "alex-mcp": {
      "command": "/path/to/alex-mcp/run_alex_mcp.sh"
    }
  }
}
```

Replace `/path/to/alex-mcp` with the actual path to the repository on your system.

## Available Tools

The OpenAlex MCP server provides the following tools:

1. **disambiguate_author**: Disambiguate an author using OpenAlex's ML-powered disambiguation system.
2. **search_authors**: Search for authors with advanced filtering capabilities.
3. **get_author_profile**: Get detailed author profile by OpenAlex ID.
4. **resolve_institution**: Resolve institution name or abbreviation to full OpenAlex data.

## Troubleshooting

If you encounter any issues, make sure:

1. You're using Python 3.10 or higher
2. The virtual environment is activated
3. All dependencies are installed correctly

For more information, see the [README.md](README.md) file.
