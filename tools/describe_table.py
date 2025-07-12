"""Describe table tool"""

from typing import Any, List, Optional, Union
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from database_manager import DatabaseManager
from .common import ErrorResponse


class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool
    default: Optional[Any] = None
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


def describe_table(
    db_manager: DatabaseManager, database: str, table_name: str, db_schema: Optional[str] = None
) -> Union[TableDescription, ErrorResponse]:
    """Get table structure including columns and foreign keys"""

    engine = db_manager.get_engine(database)
    if not engine:
        return ErrorResponse(error=f"Database '{database}' not found")

    try:
        inspector = inspect(engine)

        columns = []
        for col in inspector.get_columns(table_name, schema=db_schema):
            columns.append(
                ColumnInfo(
                    name=col["name"],
                    type=str(col["type"]),
                    nullable=col.get("nullable", True),
                    default=col.get("default"),
                    primary_key=col.get("primary_key", False),
                )
            )

        foreign_keys = []
        for fk in inspector.get_foreign_keys(table_name, schema=db_schema):
            foreign_keys.append(
                ForeignKey(
                    constrained_columns=fk["constrained_columns"],
                    referred_table=fk["referred_table"],
                    referred_columns=fk["referred_columns"],
                )
            )

        incoming_fks = []
        table_names = inspector.get_table_names(schema=db_schema)
        for table in table_names:
            for fk in inspector.get_foreign_keys(table, schema=db_schema):
                if fk["referred_table"] == table_name:
                    incoming_fks.append(
                        IncomingForeignKey(
                            from_table=table,
                            from_columns=fk["constrained_columns"],
                            to_columns=fk["referred_columns"],
                        )
                    )

        table_ref = f"{db_schema}.{table_name}" if db_schema else table_name
        return TableDescription(
            table=table_ref,
            columns=columns,
            foreign_keys=foreign_keys,
            incoming_foreign_keys=incoming_fks,
        )

    except SQLAlchemyError as e:
        return ErrorResponse(error=f"Table description failed: {str(e)}")
