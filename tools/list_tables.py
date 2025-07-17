from typing import List
from pydantic import BaseModel
from database_manager import DatabaseManager


class ListTablesError(Exception):
    pass


class SchemaInfo(BaseModel):
    db_schema: str
    tables: List[str]

    def __str__(self) -> str:
        if len(self.tables) == 0:
            return f"Schema {self.db_schema}: (no tables)"
        elif len(self.tables) == 1:
            return f"Schema {self.db_schema}: {self.tables[0]}"
        else:
            return f"Schema {self.db_schema}: {', '.join(self.tables)}"


class TablesResponse(BaseModel):
    database: str
    schemas: List[SchemaInfo]

    def __str__(self) -> str:
        if not self.schemas:
            return f"Database '{self.database}': (no schemas found)"

        total_tables = sum(len(schema.tables) for schema in self.schemas)
        if total_tables == 0:
            return f"Database '{self.database}': (no tables found)"

        schema_lines = [str(schema) for schema in self.schemas]
        return f"Database '{self.database}':\n" + "\n".join(schema_lines)


async def list_tables(
    db_manager: DatabaseManager, database: str, schema: str = None
) -> TablesResponse:
    """List all tables in the specified database and optional schema"""

    def _list_tables_operation(inspector):
        schemas = []

        if schema:
            try:
                tables = inspector.get_table_names(schema=schema)
                schemas.append(SchemaInfo(db_schema=schema, tables=tables))
            except Exception as e:
                raise ListTablesError(
                    f"Unable to list tables in '{schema}', '{database}': {str(e)}"
                ) from e
        else:
            available_schemas = inspector.get_schema_names()

            for schema_name in available_schemas:
                schema_tables = inspector.get_table_names(schema=schema_name)
                if schema_tables:
                    schemas.append(
                        SchemaInfo(
                            db_schema=schema_name or "default", tables=schema_tables
                        )
                    )

        return schemas

    schemas = await db_manager.run_inspector_operation(database, _list_tables_operation)
    return TablesResponse(database=database, schemas=schemas)
