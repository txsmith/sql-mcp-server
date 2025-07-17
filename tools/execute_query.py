from typing import Dict, Any, List
from sqlalchemy import text
from pydantic import BaseModel
from database_manager import DatabaseManager


class QueryResponse(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    truncated: bool


class QueryError(Exception):
    pass


async def execute_query(
    db_manager: DatabaseManager, database: str, query: str
) -> QueryResponse:
    """Execute a SELECT query on the specified database"""

    max_rows = db_manager.config.settings.get("max_rows_per_query", 1000)

    async with db_manager.connect(database) as conn:
        try:
            result = await conn.execute(text(query))
            rows = result.fetchmany(max_rows)
            columns = list(result.keys())

            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))

            return QueryResponse(
                columns=columns,
                rows=data,
                row_count=len(data),
                truncated=len(data) == max_rows,
            )
        except Exception as e:
            raise QueryError(f"Error executing query: {str(e)}") from e
