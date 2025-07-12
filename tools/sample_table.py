"""Sample table tool"""

from typing import Dict, Any, Optional, List, Union
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from database_manager import DatabaseManager
from .common import ErrorResponse


class SampleResponse(BaseModel):
    table: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int


def sample_table(
    db_manager: DatabaseManager,
    database: str,
    table_name: str,
    limit: Optional[int] = None,
    db_schema: Optional[str] = None,
) -> Union[SampleResponse, ErrorResponse]:
    """Sample rows from a table"""

    engine = db_manager.get_engine(database)
    if not engine:
        return ErrorResponse(error=f"Database '{database}' not found")

    sample_size = limit or db_manager.config.settings.get("sample_size", 10)

    try:
        with engine.connect() as conn:
            table_ref = f"{db_schema}.{table_name}" if db_schema else table_name
            query = text(f"SELECT * FROM {table_ref} LIMIT {sample_size}")
            result = conn.execute(query)
            rows = result.fetchall()
            columns = list(result.keys())

            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))

            return SampleResponse(
                table=table_ref, columns=columns, rows=data, row_count=len(data)
            )

    except SQLAlchemyError as e:
        return ErrorResponse(error=f"Table sampling failed: {str(e)}")
