# Database Explorer MCP Server

A FastMCP server for exploring multiple databases with support for SELECT queries, table sampling, and structure inspection.

## Features

- **Multiple Database Support**: Configure multiple databases with connection strings or individual fields
- **Safe Query Execution**: Only SELECT queries allowed for read-only exploration
- **Table Sampling**: Sample rows from tables with configurable limits
- **Schema Inspection**: View table structure, columns, and foreign key relationships
- **Connection Management**: Automatic connection pooling and timeout handling

## Installation

1. Install dependencies using uv:
```bash
uv sync
```

2. Configure your databases in `config.yaml`:
```yaml
databases:
  my_postgres:
    type: "postgresql"
    description: "My PostgreSQL database"
    host: "localhost"
    port: 5432
    database: "mydb"
    username: "user"
    password: "p@ss!w$rd%"
    extra_params:
      sslmode: "require"
```

See `config_example.yaml` for more examples of both formats.

3. Run the server:
```bash
fastmcp dev main.py
```


## Installing as MCP Server in Claude

From the repo root:
```bash
claude mcp add --scope user sql-explorer fastmcp run $(pwd)/main.py
```

## Supported Databases

- PostgreSQL (via psycopg2)
- MySQL (via PyMySQL)
- SQLite (local files and in-memory)
- SQL Server (via pyodbc)
- Snowflake (data warehouse)


## Available Tools

### `list_databases()`
Lists all configured databases with their types and descriptions.

### `execute_query(database: str, query: str)`
Executes a query on the specified database.
** WARNING: ** this will execute any arbitrary SQL, only connect to your DB using read-only permissions! 
- **database**: Name of the database from config
- **query**: query to execute

### `sample_table(database: str, table_name: str, limit: Optional[int])`
Samples rows from a table.
- **database**: Name of the database
- **table_name**: Name of the table to sample
- **limit**: Number of rows to sample (optional)

### `describe_table(database: str, table_name: str)`
Gets table structure including columns and foreign keys.
- **database**: Name of the database
- **table_name**: Name of the table to describe

### `list_tables(database: str, schema: Optional[str])`
Lists all tables in the specified database with hierarchical schema structure.
- **database**: Name of the database
- **schema**: Optional schema name to filter by

Returns a hierarchical structure with schemas containing their tables and table counts.

## Security considerations
Configure your databases with read-only users to prevent destructive operations. The server does not restrict query types at the application level. Also make sure to keep your config.yaml private as this will likely contain sensitive information. 

## Development

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run black .
uv run flake8
```

