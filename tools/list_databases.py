from typing import List, Dict
from database_manager import DatabaseManager


def list_databases(db_manager: DatabaseManager) -> List[Dict[str, str]]:
    """List all configured databases"""
    result = []
    for db_name, db_config in db_manager.config.databases.items():
        result.append(
            {
                "name": db_name,
                "type": db_config.type,
                "description": db_config.description,
            }
        )
    return result
