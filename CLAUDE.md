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

## Architecture Overview

### Core Components

- **`main.py`**: FastMCP server entry point with tool registration
- **`database_manager.py`**: Centralized database connection management with SQLAlchemy engines
- **`tools/`**: Business logic modules for each MCP tool:
  - `list_databases.py` - List configured databases
  - `execute_query.py` - Execute SELECT queries 
  - `sample_table.py` - Sample table rows with limits
  - `describe_table.py` - Get table schema and foreign keys
  - `list_tables.py` - List tables with hierarchical schema structure

### Configuration

- **`config.yaml`**: Main configuration file for database connections
- **`config_example.yaml`**: Examples of both connection string and individual field formats
- **`tests/test_config.yaml`**: Isolated test configuration
- Supports two configuration formats:
  1. Connection string format: `connection_string: "sqlite:///path/to/db"`
  2. Individual fields: `host`, `port`, `database`, `username`, `password`, etc.

### Database Support

Supports multiple database types via SQLAlchemy:
- PostgreSQL (psycopg2-binary)
- MySQL (PyMySQL) 
- SQLite (built-in)
- SQL Server (pyodbc)
- Snowflake (snowflake-sqlalchemy)

### Security Model

- Read-only operations enforced by user permissions, not application logic
- Connection pooling with configurable timeouts
- Logging disabled for database connectors to prevent stdout pollution
- Test isolation using separate configuration files

## Development Workflow

### Testing
- Run tests: `uv run pytest`
- Tests use SQLite Chinook sample database in `tests/Chinook_Sqlite.sqlite`
- Each tool has dedicated test file in `tests/test_*.py`

### Code Quality
- Format: `uv run black .`
- Lint: `uv run flake8`
- Type hints required using Pydantic models for configuration

### Build and Package Management

- We're using uv for build/env/package management. Do not use anything else.
- Dependencies managed in `pyproject.toml`
- Dev dependencies include pytest, black, flake8
