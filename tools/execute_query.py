from typing import Dict, Any, List
from pydantic import BaseModel
from database_manager import DatabaseManager


class QueryResponse(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    truncated: bool


async def execute_query(
    db_manager: DatabaseManager, database: str, query: str
) -> QueryResponse:
    """Execute a SELECT query on the specified database"""

    max_rows = db_manager.config.settings.get("max_rows_per_query", 1000)

    result = await db_manager.execute_query(database, query)
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
