# Claude Code Notes

## Code Style Preferences

- **NO comments**: You shall not add code comments. Only on request, or when you've identified a non-obvious gotcha
- **Run 'black' after Python edits**: Any time you make an edit to a Python file, run flake8 to format it
- **Prefer typed/structured data**: Use typed/structured data over dicts. Types make it easier to write tests and debug

## Project Context

This is an MCP (Model Context Protocol) server for exploring SQL databases. The architecture separates business logic from MCP concerns:

- Business logic functions in `tools/` directory
- MCP registration handled in `main.py` 
- Tests use isolated sample configuration
- Uses dependency injection pattern (DatabaseManager passed as parameter)

## Build and Package Management

- We're using uv for build/env/package management. Do not use anything else.
