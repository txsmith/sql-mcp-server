from typing import Any, List
import math
from pydantic import BaseModel
from database_manager import DatabaseManager


class TableNotFoundError(Exception):
    pass


class DescribeTableError(Exception):
    pass


class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool
    default: Any = None
    primary_key: bool = False


class ForeignKey(BaseModel):
    constrained_columns: List[str]
    referred_table: str
    referred_columns: List[str]


class IncomingForeignKey(BaseModel):
    from_table: str
    from_columns: List[str]
    to_columns: List[str]


class TableDescription(BaseModel):
    table: str
    columns: List[ColumnInfo]
    foreign_keys: List[ForeignKey]
    incoming_foreign_keys: List[IncomingForeignKey]
    total_count: int
    current_page: int
    total_pages: int


DIALECT_QUERIES = {
    "postgresql": {
        "table_exists": """
            SELECT table_name FROM information_schema.tables 
            WHERE table_name = '{table_name}' 
            AND table_schema NOT IN ('information_schema', 'pg_catalog')
            AND ('{schema_name}' = '' OR table_schema = '{schema_name}')
            LIMIT 1
        """,
        "columns": """
            SELECT 
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default
            FROM information_schema.columns c
            WHERE c.table_schema NOT IN ('information_schema', 'pg_catalog')
            AND c.table_name = '{table_name}'
            AND ('{schema_name}' = '' OR c.table_schema = '{schema_name}')
            ORDER BY c.ordinal_position
            LIMIT {limit} OFFSET {offset}
        """,
        "columns_count": """
            SELECT COUNT(*)
            FROM information_schema.columns c
            WHERE c.table_schema NOT IN ('information_schema', 'pg_catalog')
            AND c.table_name = '{table_name}'
            AND ('{schema_name}' = '' OR c.table_schema = '{schema_name}')
        """,
        "foreign_key": """
            SELECT 
                n.nspname as source_schema_name,
                t.relname as source_table_name,
                a.attname as source_column_name,
                fn.nspname as dest_schema_name,
                ft.relname as dest_table_name,
                fa.attname as dest_column_name,
                c.conname as constraint_name
            FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            JOIN pg_namespace n ON t.relnamespace = n.oid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(c.conkey)
            JOIN pg_class ft ON c.confrelid = ft.oid
            JOIN pg_namespace fn ON ft.relnamespace = fn.oid
            JOIN pg_attribute fa ON fa.attrelid = ft.oid AND fa.attnum = ANY(c.confkey)
            WHERE c.contype = 'f'
            AND ('{source_table_name}' = '' OR t.relname = '{source_table_name}')
            AND ('{dest_table_name}' = '' OR ft.relname = '{dest_table_name}')
            AND ('{source_schema_name}' = '' OR n.nspname = '{source_schema_name}')
            AND ('{dest_schema_name}' = '' OR fn.nspname = '{dest_schema_name}')
            ORDER BY c.conname
            LIMIT {limit} OFFSET {offset}
        """,
        "foreign_key_count": """
            SELECT COUNT(*)
            FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            JOIN pg_namespace n ON t.relnamespace = n.oid
            JOIN pg_class ft ON c.confrelid = ft.oid
            JOIN pg_namespace fn ON ft.relnamespace = fn.oid
            WHERE c.contype = 'f'
            AND ('{source_table_name}' = '' OR t.relname = '{source_table_name}')
            AND ('{dest_table_name}' = '' OR ft.relname = '{dest_table_name}')
            AND ('{source_schema_name}' = '' OR n.nspname = '{source_schema_name}')
            AND ('{dest_schema_name}' = '' OR fn.nspname = '{dest_schema_name}')
        """,
        "primary_key": """
            SELECT 
                c.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.columns c ON kcu.column_name = c.column_name AND kcu.table_name = c.table_name
            WHERE tc.constraint_type = 'PRIMARY KEY'
            AND tc.table_name = '{table_name}'
            AND ('{schema_name}' = '' OR tc.table_schema = '{schema_name}')
            ORDER BY kcu.ordinal_position
        """,
    },
    "mysql": {
        "table_exists": """
            SELECT table_name FROM information_schema.tables 
            WHERE table_name = '{table_name}' 
            AND table_schema NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
            AND ('{schema_name}' = '' OR table_schema = '{schema_name}')
            LIMIT 1
        """,
        "columns": """
            SELECT 
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default
            FROM information_schema.columns c
            WHERE c.table_schema NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
            AND c.table_name = '{table_name}'
            AND ('{schema_name}' = '' OR c.table_schema = '{schema_name}')
            ORDER BY c.ordinal_position
            LIMIT {limit} OFFSET {offset}
        """,
        "columns_count": """
            SELECT COUNT(*)
            FROM information_schema.columns c
            WHERE c.table_schema NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
            AND c.table_name = '{table_name}'
            AND ('{schema_name}' = '' OR c.table_schema = '{schema_name}')
        """,
        "foreign_key": """
            SELECT 
                kcu.table_schema as source_schema_name,
                kcu.table_name as source_table_name,
                kcu.column_name as source_column_name,
                kcu.referenced_table_schema as dest_schema_name,
                kcu.referenced_table_name as dest_table_name,
                kcu.referenced_column_name as dest_column_name,
                kcu.constraint_name
            FROM information_schema.key_column_usage kcu
            WHERE kcu.referenced_table_name IS NOT NULL
            AND kcu.table_schema NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
            AND ('{source_table_name}' = '' OR kcu.table_name = '{source_table_name}')
            AND ('{dest_table_name}' = '' OR kcu.referenced_table_name = '{dest_table_name}')
            AND ('{source_schema_name}' = '' OR kcu.table_schema = '{source_schema_name}')
            AND ('{dest_schema_name}' = '' OR kcu.referenced_table_schema = '{dest_schema_name}')
            ORDER BY kcu.constraint_name
            LIMIT {limit} OFFSET {offset}
        """,
        "foreign_key_count": """
            SELECT COUNT(*)
            FROM information_schema.key_column_usage kcu
            WHERE kcu.referenced_table_name IS NOT NULL
            AND kcu.table_schema NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
            AND ('{source_table_name}' = '' OR kcu.table_name = '{source_table_name}')
            AND ('{dest_table_name}' = '' OR kcu.referenced_table_name = '{dest_table_name}')
            AND ('{source_schema_name}' = '' OR kcu.table_schema = '{source_schema_name}')
            AND ('{dest_schema_name}' = '' OR kcu.referenced_table_schema = '{dest_schema_name}')
        """,
        "primary_key": """
            SELECT 
                c.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY'
            AND tc.table_name = '{table_name}'
            AND ('{schema_name}' = '' OR tc.table_schema = '{schema_name}')
            ORDER BY kcu.ordinal_position
        """,
    },
    "sqlite": {
        "table_exists": """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name = '{table_name}' 
            LIMIT 1
        """,
        "columns": """
            SELECT 
                p.name as column_name,
                p.type as data_type,
                CASE WHEN p."notnull" = 0 THEN 'YES' ELSE 'NO' END as is_nullable,
                p.dflt_value as column_default
            FROM pragma_table_info('{table_name}') p
            ORDER BY p.cid
            LIMIT {limit} OFFSET {offset}
        """,
        "columns_count": """
            SELECT COUNT(*)
            FROM pragma_table_info('{table_name}')
        """,
        "foreign_key": """
            SELECT 
                'main' as source_schema_name,
                m.name as source_table_name,
                fk."from" as source_column_name,
                'main' as dest_schema_name,
                fk."table" as dest_table_name,
                fk."to" as dest_column_name,
                'fk_' || m.name || '_' || fk.id as constraint_name
            FROM sqlite_master m
            JOIN pragma_foreign_key_list(m.name) fk
            WHERE m.type = 'table' AND m.name NOT LIKE 'sqlite_%'
            AND ('{source_table_name}' = '' OR m.name = '{source_table_name}')
            AND ('{dest_table_name}' = '' OR fk."table" = '{dest_table_name}')
            ORDER BY constraint_name
            LIMIT {limit} OFFSET {offset}
        """,
        "foreign_key_count": """
            SELECT COUNT(*)
            FROM sqlite_master m
            JOIN pragma_foreign_key_list(m.name) fk
            WHERE m.type = 'table' AND m.name NOT LIKE 'sqlite_%'
            AND ('{source_table_name}' = '' OR m.name = '{source_table_name}')
            AND ('{dest_table_name}' = '' OR fk."table" = '{dest_table_name}')
        """,
        "primary_key": """
            SELECT 
                p.name as column_name
            FROM pragma_table_info('{table_name}') p
            WHERE p.pk = 1
            ORDER BY p.pk
        """,
    },
    "mssql": {
        "table_exists": """
            SELECT t.name FROM sys.tables t
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE t.name = '{table_name}' 
            AND s.name NOT IN ('information_schema', 'sys')
            AND ('{schema_name}' = '' OR s.name = '{schema_name}')
        """,
        "columns": """
            SELECT 
                c.name as column_name,
                tp.name as data_type,
                CASE WHEN c.is_nullable = 1 THEN 'YES' ELSE 'NO' END as is_nullable,
                dc.definition as column_default
            FROM sys.tables t
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            INNER JOIN sys.columns c ON t.object_id = c.object_id
            INNER JOIN sys.types tp ON c.user_type_id = tp.user_type_id
            LEFT JOIN sys.default_constraints dc ON c.default_object_id = dc.object_id
            WHERE s.name NOT IN ('information_schema', 'sys')
            AND t.name = '{table_name}'
            AND ('{schema_name}' = '' OR s.name = '{schema_name}')
            ORDER BY c.column_id
            OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
        """,
        "columns_count": """
            SELECT COUNT(*)
            FROM sys.tables t
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            INNER JOIN sys.columns c ON t.object_id = c.object_id
            WHERE s.name NOT IN ('information_schema', 'sys')
            AND t.name = '{table_name}'
            AND ('{schema_name}' = '' OR s.name = '{schema_name}')
        """,
        "foreign_key": """
            SELECT 
                s.name as source_schema_name,
                t.name as source_table_name,
                c.name as source_column_name,
                rs.name as dest_schema_name,
                rt.name as dest_table_name,
                rc.name as dest_column_name,
                fk.name as constraint_name
            FROM sys.foreign_keys fk
            JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
            JOIN sys.tables t ON fk.parent_object_id = t.object_id
            JOIN sys.schemas s ON t.schema_id = s.schema_id
            JOIN sys.columns c ON fkc.parent_object_id = c.object_id AND fkc.parent_column_id = c.column_id
            JOIN sys.tables rt ON fk.referenced_object_id = rt.object_id
            JOIN sys.schemas rs ON rt.schema_id = rs.schema_id
            JOIN sys.columns rc ON fkc.referenced_object_id = rc.object_id AND fkc.referenced_column_id = rc.column_id
            WHERE s.name NOT IN ('information_schema', 'sys')
            AND ('{source_table_name}' = '' OR t.name = '{source_table_name}')
            AND ('{dest_table_name}' = '' OR rt.name = '{dest_table_name}')
            AND ('{source_schema_name}' = '' OR s.name = '{source_schema_name}')
            AND ('{dest_schema_name}' = '' OR rs.name = '{dest_schema_name}')
            ORDER BY fk.name
            OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
        """,
        "foreign_key_count": """
            SELECT COUNT(*)
            FROM sys.foreign_keys fk
            JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
            JOIN sys.tables t ON fk.parent_object_id = t.object_id
            JOIN sys.schemas s ON t.schema_id = s.schema_id
            JOIN sys.tables rt ON fk.referenced_object_id = rt.object_id
            JOIN sys.schemas rs ON rt.schema_id = rs.schema_id
            WHERE s.name NOT IN ('information_schema', 'sys')
            AND ('{source_table_name}' = '' OR t.name = '{source_table_name}')
            AND ('{dest_table_name}' = '' OR rt.name = '{dest_table_name}')
            AND ('{source_schema_name}' = '' OR s.name = '{source_schema_name}')
            AND ('{dest_schema_name}' = '' OR rs.name = '{dest_schema_name}')
        """,
        "primary_key": """
            SELECT 
                c.name as column_name
            FROM sys.key_constraints kc
            JOIN sys.index_columns ic ON kc.parent_object_id = ic.object_id AND kc.unique_index_id = ic.index_id
            JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            JOIN sys.tables t ON kc.parent_object_id = t.object_id
            JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE kc.type = 'PK'
            AND t.name = '{table_name}'
            AND ('{schema_name}' = '' OR s.name = '{schema_name}')
            ORDER BY ic.key_ordinal
        """,
    },
    "snowflake": {
        "table_exists": """
            SELECT table_name FROM information_schema.tables 
            WHERE table_name = '{table_name}' 
            AND table_schema NOT IN ('INFORMATION_SCHEMA')
            AND ('{schema_name}' = '' OR table_schema = '{schema_name}')
            LIMIT 1
        """,
        "columns": """
            SELECT 
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default
            FROM information_schema.columns c
            WHERE c.table_schema NOT IN ('INFORMATION_SCHEMA')
            AND c.table_name = '{table_name}'
            AND ('{schema_name}' = '' OR c.table_schema = '{schema_name}')
            ORDER BY c.ordinal_position
            LIMIT {limit} OFFSET {offset}
        """,
        "columns_count": """
            SELECT COUNT(*)
            FROM information_schema.columns c
            WHERE c.table_schema NOT IN ('INFORMATION_SCHEMA')
            AND c.table_name = '{table_name}'
            AND ('{schema_name}' = '' OR c.table_schema = '{schema_name}')
        """,
        "foreign_key": """
            SELECT 
                tc.table_schema as source_schema_name,
                tc.table_name as source_table_name,
                kcu.column_name as source_column_name,
                ccu.table_schema as dest_schema_name,
                ccu.table_name as dest_table_name,
                ccu.column_name as dest_column_name,
                tc.constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema NOT IN ('INFORMATION_SCHEMA')
            AND ('{source_table_name}' = '' OR tc.table_name = '{source_table_name}')
            AND ('{dest_table_name}' = '' OR ccu.table_name = '{dest_table_name}')
            AND ('{source_schema_name}' = '' OR tc.table_schema = '{source_schema_name}')
            AND ('{dest_schema_name}' = '' OR ccu.table_schema = '{dest_schema_name}')
            ORDER BY tc.constraint_name
            LIMIT {limit} OFFSET {offset}
        """,
        "foreign_key_count": """
            SELECT COUNT(*)
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema NOT IN ('INFORMATION_SCHEMA')
            AND ('{source_table_name}' = '' OR tc.table_name = '{source_table_name}')
            AND ('{dest_table_name}' = '' OR ccu.table_name = '{dest_table_name}')
            AND ('{source_schema_name}' = '' OR tc.table_schema = '{source_schema_name}')
            AND ('{dest_schema_name}' = '' OR ccu.table_schema = '{dest_schema_name}')
        """,
        "primary_key": """
            SELECT 
                kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY'
            AND tc.table_name = '{table_name}'
            AND ('{schema_name}' = '' OR tc.table_schema = '{schema_name}')
            ORDER BY kcu.ordinal_position
        """,
    },
}


async def _get_primary_keys(
    db_manager: DatabaseManager,
    database: str,
    table_name: str,
    db_schema: str,
    dialect: str,
    queries: dict,
) -> set:
    """Get primary key columns for a table"""
    try:
        pk_query = queries["primary_key"].format(
            table_name=table_name, schema_name=db_schema
        )
        result = await db_manager.execute_query(database, pk_query)
        rows = result.fetchall()
        return {row[0] for row in rows}
    except Exception as e:
        raise DescribeTableError(
            f"Failed to get primary keys for table '{table_name}' in database '{database}': {str(e)}"
        ) from e


async def _get_columns(
    db_manager: DatabaseManager,
    database: str,
    table_name: str,
    db_schema: str,
    dialect: str,
    queries: dict,
    primary_keys: set,
    limit: int,
    offset: int,
) -> List[ColumnInfo]:
    """Get column information for a table"""
    try:
        query = queries["columns"].format(
            table_name=table_name,
            schema_name=db_schema,
            limit=limit,
            offset=offset,
        )
        result = await db_manager.execute_query(database, query)
        rows = result.fetchall()

        columns = []
        for row in rows:
            column_name = row[0]
            data_type = row[1]
            is_nullable = row[2]
            column_default = row[3]

            nullable = is_nullable == "YES" if is_nullable else True
            is_primary_key = column_name in primary_keys

            columns.append(
                ColumnInfo(
                    name=column_name,
                    type=data_type,
                    nullable=nullable,
                    default=column_default,
                    primary_key=is_primary_key,
                )
            )
        return columns
    except Exception as e:
        raise DescribeTableError(
            f"Failed to get columns for table '{table_name}' in database '{database}': {str(e)}"
        ) from e


async def _get_foreign_keys(
    db_manager: DatabaseManager,
    database: str,
    table_name: str,
    db_schema: str,
    dialect: str,
    queries: dict,
    limit: int,
    offset: int,
    outgoing: bool = True,
) -> List[ForeignKey] | List[IncomingForeignKey]:
    """Get foreign key information (outgoing or incoming)"""
    try:
        if outgoing:
            query = queries["foreign_key"].format(
                source_table_name=table_name,
                dest_table_name="",
                source_schema_name=db_schema,
                dest_schema_name="",
                limit=limit,
                offset=offset,
            )
        else:
            query = queries["foreign_key"].format(
                source_table_name="",
                dest_table_name=table_name,
                source_schema_name="",
                dest_schema_name=db_schema,
                limit=limit,
                offset=offset,
            )

        result = await db_manager.execute_query(database, query)
        rows = result.fetchall()

        if outgoing:
            fks = []
            fk_groups = {}
            for row in rows:
                constraint_name = row[6]
                if constraint_name not in fk_groups:
                    fk_groups[constraint_name] = {
                        "constrained_columns": [],
                        "referred_table": row[4],
                        "referred_columns": [],
                    }
                fk_groups[constraint_name]["constrained_columns"].append(row[2])
                fk_groups[constraint_name]["referred_columns"].append(row[5])

            for constraint_name, fk_data in fk_groups.items():
                fks.append(
                    ForeignKey(
                        constrained_columns=fk_data["constrained_columns"],
                        referred_table=fk_data["referred_table"],
                        referred_columns=fk_data["referred_columns"],
                    )
                )
            return fks
        else:
            incoming_fks = []
            fk_groups = {}
            for row in rows:
                constraint_name = row[6]
                from_table = row[1]
                if constraint_name not in fk_groups:
                    fk_groups[constraint_name] = {
                        "from_table": from_table,
                        "from_columns": [],
                        "to_columns": [],
                    }
                fk_groups[constraint_name]["from_columns"].append(row[2])
                fk_groups[constraint_name]["to_columns"].append(row[5])

            for constraint_name, fk_data in fk_groups.items():
                incoming_fks.append(
                    IncomingForeignKey(
                        from_table=fk_data["from_table"],
                        from_columns=fk_data["from_columns"],
                        to_columns=fk_data["to_columns"],
                    )
                )
            return incoming_fks
    except Exception as e:
        fk_type = "outgoing" if outgoing else "incoming"
        raise DescribeTableError(
            f"Failed to get {fk_type} foreign keys for table '{table_name}' in database '{database}': {str(e)}"
        ) from e


async def _get_counts(
    db_manager: DatabaseManager,
    database: str,
    table_name: str,
    db_schema: str,
    dialect: str,
    queries: dict,
) -> tuple[int, int, int]:
    """Get counts for columns, outgoing FKs, and incoming FKs"""
    try:
        column_count_query = queries["columns_count"].format(
            table_name=table_name, schema_name=db_schema
        )
        outgoing_fk_count_query = queries["foreign_key_count"].format(
            source_table_name=table_name,
            dest_table_name="",
            source_schema_name=db_schema,
            dest_schema_name="",
        )
        incoming_fk_count_query = queries["foreign_key_count"].format(
            source_table_name="",
            dest_table_name=table_name,
            source_schema_name="",
            dest_schema_name=db_schema,
        )

        column_result = await db_manager.execute_query(database, column_count_query)
        outgoing_fk_result = await db_manager.execute_query(
            database, outgoing_fk_count_query
        )
        incoming_fk_result = await db_manager.execute_query(
            database, incoming_fk_count_query
        )

        column_count = column_result.scalar()
        outgoing_fk_count = outgoing_fk_result.scalar()
        incoming_fk_count = incoming_fk_result.scalar()

        return column_count, outgoing_fk_count, incoming_fk_count
    except Exception as e:
        raise DescribeTableError(
            f"Failed to get counts for table '{table_name}' in database '{database}': {str(e)}"
        ) from e


async def _check_table_exists(
    db_manager: DatabaseManager,
    database: str,
    table_name: str,
    db_schema: str,
    queries: dict,
) -> bool:
    """Check if a table exists using a simple query"""
    try:
        query = queries["table_exists"].format(
            table_name=table_name, schema_name=db_schema
        )
        result = await db_manager.execute_query(database, query)
        rows = result.fetchall()
        return len(rows) > 0
    except Exception as e:
        raise DescribeTableError(
            f"Failed to check if table '{table_name}' exists in database '{database}': {str(e)}"
        ) from e


async def describe_table(
    db_manager: DatabaseManager,
    database: str,
    table_name: str,
    db_schema: str | None = None,
    limit: int = 250,
    page: int = 1,
) -> TableDescription:
    """Get table structure including columns and foreign keys with pagination"""

    if limit < 1:
        raise DescribeTableError("Limit must be greater than 0")

    if page < 1:
        raise DescribeTableError("Page number must be greater than 0")

    max_rows = db_manager.config.settings.get("max_rows_per_query", 1000)
    if limit > max_rows:
        limit = max_rows

    dialect = db_manager.get_dialect_name(database)

    if dialect not in DIALECT_QUERIES:
        raise DescribeTableError(f"Unsupported database dialect: {dialect}")

    queries = DIALECT_QUERIES[dialect]

    schema_value = db_schema if db_schema else ""

    table_exists = await _check_table_exists(
        db_manager, database, table_name, schema_value, queries
    )
    if not table_exists:
        raise TableNotFoundError(
            f"Table '{table_name}' not found in database '{database}'"
        )

    column_count, outgoing_fk_count, incoming_fk_count = await _get_counts(
        db_manager, database, table_name, schema_value, dialect, queries
    )

    total_count = column_count + outgoing_fk_count + incoming_fk_count
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 1

    offset = (page - 1) * limit

    columns = []
    foreign_keys = []
    incoming_foreign_keys = []

    primary_keys = await _get_primary_keys(
        db_manager, database, table_name, schema_value, dialect, queries
    )

    remaining_limit = limit
    current_offset = offset

    if current_offset < column_count and remaining_limit > 0:
        columns_to_fetch = min(remaining_limit, column_count - current_offset)
        columns = await _get_columns(
            db_manager,
            database,
            table_name,
            schema_value,
            dialect,
            queries,
            primary_keys,
            columns_to_fetch,
            current_offset,
        )
        remaining_limit -= len(columns)
        current_offset = 0
    else:
        current_offset -= column_count

    if current_offset < outgoing_fk_count and remaining_limit > 0:
        fks_to_fetch = min(remaining_limit, outgoing_fk_count - current_offset)
        foreign_keys = await _get_foreign_keys(
            db_manager,
            database,
            table_name,
            schema_value,
            dialect,
            queries,
            fks_to_fetch,
            current_offset,
            outgoing=True,
        )
        remaining_limit -= len(foreign_keys)
        current_offset = 0
    else:
        current_offset -= outgoing_fk_count

    if current_offset < incoming_fk_count and remaining_limit > 0:
        incoming_fks_to_fetch = min(remaining_limit, incoming_fk_count - current_offset)
        incoming_foreign_keys = await _get_foreign_keys(
            db_manager,
            database,
            table_name,
            schema_value,
            dialect,
            queries,
            incoming_fks_to_fetch,
            current_offset,
            outgoing=False,
        )

    table_ref = f"{db_schema}.{table_name}" if db_schema else table_name
    return TableDescription(
        table=table_ref,
        columns=columns,
        foreign_keys=foreign_keys,
        incoming_foreign_keys=incoming_foreign_keys,
        total_count=total_count,
        current_page=page,
        total_pages=total_pages,
    )
