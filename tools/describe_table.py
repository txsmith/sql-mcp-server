from typing import Any, List
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


def _check_table_exists(inspector, table_name, db_schema, database):
    """Explicitly check if a table exists"""
    try:
        table_names = inspector.get_table_names(schema=db_schema)
        if table_name not in table_names:
            raise TableNotFoundError(
                f"Table '{table_name}' not found in database '{database}'"
            )
    except TableNotFoundError:
        raise
    except Exception as e:
        raise DescribeTableError(
            f"Failed to check if table '{table_name}' exists in database '{database}'"
        ) from e


def _get_columns(inspector, table_name, db_schema, database):
    try:
        columns_data = inspector.get_columns(table_name, schema=db_schema)
    except Exception as e:
        raise DescribeTableError(
            f"Failed to get columns for table '{table_name}' in database '{database}'"
        ) from e

    columns = []
    for col in columns_data:
        columns.append(
            ColumnInfo(
                name=col["name"],
                type=str(col["type"]),
                nullable=col.get("nullable", True),
                default=col.get("default"),
                primary_key=col.get("primary_key", False),
            )
        )
    return columns


def _get_foreign_keys(inspector, table_name, db_schema, database):
    try:
        fks_data = inspector.get_foreign_keys(table_name, schema=db_schema)
    except Exception as e:
        raise DescribeTableError(
            f"Failed to get foreign keys for table '{table_name}' in database '{database}'"
        ) from e

    foreign_keys = []
    for fk in fks_data:
        foreign_keys.append(
            ForeignKey(
                constrained_columns=fk["constrained_columns"],
                referred_table=fk["referred_table"],
                referred_columns=fk["referred_columns"],
            )
        )
    return foreign_keys


def _get_incoming_foreign_keys(inspector, table_name, db_schema, database):
    try:
        table_names = inspector.get_table_names(schema=db_schema)
    except Exception as e:
        raise DescribeTableError(
            f"Failed to list tables in database '{database}'"
        ) from e

    incoming_fks = []
    for table in table_names:
        try:
            table_fks = inspector.get_foreign_keys(table, schema=db_schema)
            for fk in table_fks:
                if fk["referred_table"] == table_name:
                    incoming_fks.append(
                        IncomingForeignKey(
                            from_table=table,
                            from_columns=fk["constrained_columns"],
                            to_columns=fk["referred_columns"],
                        )
                    )
        except Exception as e:
            raise DescribeTableError(
                f"Failed to get foreign keys for table '{table}'"
            ) from e
    return incoming_fks


async def describe_table(
    db_manager: DatabaseManager,
    database: str,
    table_name: str,
    db_schema: str | None = None,
) -> TableDescription:
    """Get table structure including columns and foreign keys"""

    def _describe_table_operation(inspector):
        _check_table_exists(inspector, table_name, db_schema, database)

        columns = _get_columns(inspector, table_name, db_schema, database)
        foreign_keys = _get_foreign_keys(inspector, table_name, db_schema, database)
        incoming_fks = _get_incoming_foreign_keys(
            inspector, table_name, db_schema, database
        )

        table_ref = f"{db_schema}.{table_name}" if db_schema else table_name
        return TableDescription(
            table=table_ref,
            columns=columns,
            foreign_keys=foreign_keys,
            incoming_foreign_keys=incoming_fks,
        )

    return await db_manager.run_inspector_operation(database, _describe_table_operation)
