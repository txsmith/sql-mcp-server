from typing import List
import math
from pydantic import BaseModel
from database_manager import DatabaseManager


class ListTablesError(Exception):
    pass


DIALECT_QUERIES = {
    "postgresql": {
        "list": """
            SELECT schemaname as schema_name, tablename as table_name
            FROM pg_tables
            WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
            AND ('{schema_name}' = '' OR schemaname = '{schema_name}')
            ORDER BY schemaname, tablename
            LIMIT {limit} OFFSET {offset}
        """,
        "count": """
            SELECT COUNT(*)
            FROM pg_tables
            WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
            AND ('{schema_name}' = '' OR schemaname = '{schema_name}')
        """,
    },
    "mysql": {
        "list": """
            SELECT table_schema as schema_name, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
            AND table_schema NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
            AND ('{schema_name}' = '' OR table_schema = '{schema_name}')
            ORDER BY table_schema, table_name
            LIMIT {limit} OFFSET {offset}
        """,
        "count": """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
            AND table_schema NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
            AND ('{schema_name}' = '' OR table_schema = '{schema_name}')
        """,
    },
    "sqlite": {
        "list": """
            SELECT 'main' as schema_name, name as table_name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            LIMIT {limit} OFFSET {offset}
        """,
        "count": """
            SELECT COUNT(*)
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
        """,
    },
    "mssql": {
        "list": """
            SELECT s.name as schema_name, t.name as table_name
            FROM sys.tables t
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE s.name NOT IN ('information_schema', 'sys')
            AND ('{schema_name}' = '' OR s.name = '{schema_name}')
            ORDER BY s.name, t.name
            OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
        """,
        "count": """
            SELECT COUNT(*)
            FROM sys.tables t
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE s.name NOT IN ('information_schema', 'sys')
            AND ('{schema_name}' = '' OR s.name = '{schema_name}')
        """,
    },
    "snowflake": {
        "list": """
            SELECT table_schema as schema_name, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
            AND table_schema NOT IN ('INFORMATION_SCHEMA')
            AND ('{schema_name}' = '' OR table_schema = '{schema_name}')
            ORDER BY table_schema, table_name
            LIMIT {limit} OFFSET {offset}
        """,
        "count": """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
            AND table_schema NOT IN ('INFORMATION_SCHEMA')
            AND ('{schema_name}' = '' OR table_schema = '{schema_name}')
        """,
    },
}


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
    total_count: int
    current_page: int
    total_pages: int

    def __str__(self) -> str:
        if not self.schemas:
            return f"Database '{self.database}': (no schemas found)"

        total_tables = sum(len(schema.tables) for schema in self.schemas)
        if total_tables == 0:
            return f"Database '{self.database}': (no tables found)"

        schema_lines = [str(schema) for schema in self.schemas]
        result = f"Database '{self.database}':\n" + "\n".join(schema_lines)
        result += f"\n\nPage {self.current_page} of {self.total_pages} (Total: {self.total_count} tables)"
        return result


async def list_tables(
    db_manager: DatabaseManager,
    database: str,
    limit: int,
    page: int,
    schema: str = None,
) -> TablesResponse:

    if limit < 1:
        raise ListTablesError("Limit must be greater than 0")

    if page < 1:
        raise ListTablesError("Page number must be greater than 0")

    max_rows = db_manager.config.settings.get("max_rows_per_query", 1000)
    if limit > max_rows:
        limit = max_rows

    dialect = db_manager.get_dialect_name(database)

    if dialect not in DIALECT_QUERIES:
        raise ListTablesError(f"Unsupported database dialect: {dialect}")

    queries = DIALECT_QUERIES[dialect]

    offset = (page - 1) * limit

    schema_value = schema if schema else ""

    count_query = queries["count"].format(schema_name=schema_value)
    list_query = queries["list"].format(
        schema_name=schema_value, limit=limit, offset=offset
    )

    try:
        count_result = await db_manager.execute_query(database, count_query)
        total_count = count_result.scalar()

        list_result = await db_manager.execute_query(database, list_query)
        rows = list_result.fetchall()

        schema_tables = {}
        for row in rows:
            schema_name = row[0]
            table_name = row[1]
            if schema_name not in schema_tables:
                schema_tables[schema_name] = []
            schema_tables[schema_name].append(table_name)

        schemas = [
            SchemaInfo(db_schema=schema_name, tables=tables)
            for schema_name, tables in schema_tables.items()
        ]

        total_pages = math.ceil(total_count / limit) if total_count > 0 else 1

        return TablesResponse(
            database=database,
            schemas=schemas,
            total_count=total_count,
            current_page=page,
            total_pages=total_pages,
        )

    except Exception as e:
        raise ListTablesError(
            f"Unable to list tables in database '{database}': {str(e)}"
        ) from e
