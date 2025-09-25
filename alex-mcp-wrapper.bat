@echo off
REM Wrapper script for alex-mcp that activates the virtual environment on Windows

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Activate the virtual environment
call "%SCRIPT_DIR%venv\Scripts\activate.bat"

REM Run the MCP server
python -m alex_mcp.server %*
