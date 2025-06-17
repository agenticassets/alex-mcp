#!/bin/bash
# Script to run the OpenAlex MCP server in the virtual environment

# Activate the virtual environment
source venv/bin/activate

# Run the server
python run_server.py

# Deactivate the virtual environment when done
deactivate
