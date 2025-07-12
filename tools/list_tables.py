"""List tables tool"""

from typing import List, Union
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from database_manager import DatabaseManager
from .common import ErrorResponse


class SchemaInfo(BaseModel):
    db_schema: str
    tables: List[str]
    table_count: int


class TablesResponse(BaseModel):
    database: str
    schemas: List[SchemaInfo]


def list_tables(
    db_manager: DatabaseManager, database: str, schema: str = None
) -> Union[TablesResponse, ErrorResponse]:
    """List all tables in the specified database and optional schema"""

    engine = db_manager.get_engine(database)
    if not engine:
        return ErrorResponse(error=f"Database '{database}' not found")

    try:
        inspector = inspect(engine)
        schemas = []

        if schema:
            tables = inspector.get_table_names(schema=schema)
            schemas.append(
                SchemaInfo(db_schema=schema, tables=tables, table_count=len(tables))
            )
        else:
            available_schemas = inspector.get_schema_names()

            for schema_name in available_schemas:
                schema_tables = inspector.get_table_names(schema=schema_name)
                if schema_tables:
                    schemas.append(
                        SchemaInfo(
                            db_schema=schema_name or "default",
                            tables=schema_tables,
                            table_count=len(schema_tables),
                        )
                    )

        return TablesResponse(database=database, schemas=schemas)

    except SQLAlchemyError as e:
        return ErrorResponse(error=f"Failed to list tables: {str(e)}")
