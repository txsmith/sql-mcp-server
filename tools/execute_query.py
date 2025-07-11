"""Execute query tool"""

from typing import Dict, Any, List, Union
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from database_manager import DatabaseManager


class QueryResponse(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    truncated: bool


class ErrorResponse(BaseModel):
    error: str


def execute_query(
    db_manager: DatabaseManager, database: str, query: str
) -> Union[QueryResponse, ErrorResponse]:
    """Execute a SELECT query on the specified database"""

    engine = db_manager.get_engine(database)
    if not engine:
        return ErrorResponse(error=f"Database '{database}' not found")

    try:
        max_rows = db_manager.config.settings.get("max_rows_per_query", 1000)

        with engine.connect() as conn:
            result = conn.execute(text(query))
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

    except SQLAlchemyError as e:
        return ErrorResponse(error=f"Query execution failed: {str(e)}")
