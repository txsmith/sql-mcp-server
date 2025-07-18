from typing import Dict, Any, List
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
    db_schema: str | None = None,
) -> SampleResponse:
    sample_size = db_manager.config.settings.get("sample_size", 10)

    table_ref = f"{db_schema}.{table_name}" if db_schema else table_name
    query = f"SELECT * FROM {table_ref} LIMIT {sample_size}"

    try:
        result = await db_manager.execute_query(database, query)
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
