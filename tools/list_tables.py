from typing import List
from sqlalchemy import inspect
from pydantic import BaseModel
from database_manager import DatabaseManager


class ListTablesError(Exception):
    pass


class SchemaInfo(BaseModel):
    db_schema: str
    tables: List[str]
    table_count: int


class TablesResponse(BaseModel):
    database: str
    schemas: List[SchemaInfo]


async def list_tables(
    db_manager: DatabaseManager, database: str, schema: str = None
) -> TablesResponse:
    """List all tables in the specified database and optional schema"""

    async with db_manager.connect(database) as conn:

        def sync_inspect(connection):
            inspector = inspect(connection)
            schemas = []

            if schema:
                try:
                    tables = inspector.get_table_names(schema=schema)
                    schemas.append(
                        SchemaInfo(
                            db_schema=schema, tables=tables, table_count=len(tables)
                        )
                    )
                except Exception as e:
                    raise ListTablesError(
                        f"Unable to list tables in '{schema}', '{database}'"
                    ) from e
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

            return schemas

        schemas = await conn.run_sync(sync_inspect)
        return TablesResponse(database=database, schemas=schemas)
