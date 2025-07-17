"""
Database Explorer MCP Server
A FastMCP server for exploring multiple databases with SELECT queries,
table sampling, and structure inspection.
"""

import sys
import os
from typing import List, Dict
from fastmcp import FastMCP
from database_manager import load_config, DatabaseManager
import tools
from tools.execute_query import QueryResponse
from tools.sample_table import SampleResponse
from tools.describe_table import TableDescription
from tools.list_tables import TablesResponse
from tools.test_connection import ConnectionTestResponse

mcp = FastMCP("Database Explorer")

# Check for config file argument
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.yaml")
if len(sys.argv) > 2 and sys.argv[1] == "--config":
    config_path = sys.argv[2]

config = load_config(config_path)
db_manager = DatabaseManager(config)


@mcp.tool()
def list_databases() -> List[Dict[str, str]]:
    """List all configured databases"""
    return tools.list_databases(db_manager)


@mcp.tool()
def execute_query(database: str, query: str) -> QueryResponse:
    """Execute a SELECT query on the specified database"""
    return tools.execute_query(db_manager, database, query)


@mcp.tool()
async def sample_table(
    database: str,
    table_name: str,
    db_schema: str | None = None,
) -> SampleResponse:
    """Sample rows from a table"""
    return await tools.sample_table(db_manager, database, table_name, db_schema)


@mcp.tool()
async def describe_table(
    database: str, table_name: str, db_schema: str | None = None
) -> TableDescription:
    """Get table structure including columns and foreign keys"""
    return await tools.describe_table(db_manager, database, table_name, db_schema)


@mcp.tool()
async def list_tables(database: str, schema: str | None = None) -> TablesResponse:
    """List all tables in the specified database and optional schema"""
    return await tools.list_tables(db_manager, database, schema)


@mcp.tool()
async def test_connection(database: str) -> ConnectionTestResponse:
    """Test database connection"""
    return await tools.test_connection(db_manager, database)


if __name__ == "__main__":
    mcp.run()
