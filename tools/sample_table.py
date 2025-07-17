from typing import Dict, Any, List
from sqlalchemy import text
from pydantic import BaseModel
from database_manager import DatabaseManager


class SampleResponse(BaseModel):
    table: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int


class SampleTableError(Exception):
    pass


async def sample_table(
    db_manager: DatabaseManager,
    database: str,
    table_name: str,
    limit: int | None = None,
    db_schema: str | None = None,
) -> SampleResponse:
    """Sample rows from a table"""

    sample_size = limit or db_manager.config.settings.get("sample_size", 10)

    async with db_manager.connect(database) as conn:
        table_ref = f"{db_schema}.{table_name}" if db_schema else table_name
        query = text(f"SELECT * FROM {table_ref} LIMIT {sample_size}")
        try:
            result = await conn.execute(query)
            rows = result.fetchall()
            columns = list(result.keys())

            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))

            return SampleResponse(
                table=table_ref, columns=columns, rows=data, row_count=len(data)
            )
        except Exception as e:
            raise SampleTableError(f"Error sampling table: {str(e)}") from e
