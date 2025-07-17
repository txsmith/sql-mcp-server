"""Test connection tool for debugging"""

from sqlalchemy import text
from pydantic import BaseModel
from database_manager import DatabaseManager


class ConnectionTestResponse(BaseModel):
    database: str
    message: str


async def test_connection(
    db_manager: DatabaseManager, database: str
) -> ConnectionTestResponse:
    """Test database connection"""

    async with db_manager.connect(database) as conn:
        await conn.execute(text("SELECT 1"))
        return ConnectionTestResponse(
            database=database, message="Connection successful"
        )
