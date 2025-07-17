import os
import pytest

from database_manager import load_config, DatabaseManager
from tools.list_tables import list_tables, TablesResponse, ListTablesError


@pytest.fixture
def db_manager():
    """Fixture to provide database manager for tests"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "test_config.yaml")
    config = load_config(config_path)
    return DatabaseManager(config)


async def test_list_tables_result_structure(db_manager):
    """Test that list_tables returns correct structure for successful calls"""
    result = await list_tables(db_manager, "chinook_sqlite")

    assert isinstance(result, TablesResponse)
    assert result.database == "chinook_sqlite"


async def test_list_tables_chinook_database(db_manager):
    """Test that list_tables can find tables in Chinook database"""
    result = await list_tables(db_manager, "chinook_sqlite")

    assert isinstance(result, TablesResponse)
    assert len(result.schemas) > 0

    all_tables = []
    total_count = 0
    for schema in result.schemas:
        all_tables.extend(schema.tables)
        total_count += schema.table_count
        assert schema.table_count == len(schema.tables)

    expected_tables = [
        "Album",
        "Artist",
        "Customer",
        "Employee",
        "Genre",
        "Invoice",
        "InvoiceLine",
        "MediaType",
        "Playlist",
        "PlaylistTrack",
        "Track",
    ]

    for table in expected_tables:
        assert (
            table in all_tables
        ), f"Expected table '{table}' not found in Chinook database"


async def test_list_tables_empty_memory_database(db_manager):
    """Test that list_tables returns empty results for in-memory sqlite DB"""
    result = await list_tables(db_manager, "test_sqlite")

    assert isinstance(result, TablesResponse)
    assert len(result.schemas) == 0


async def test_list_tables_with_specific_schema(db_manager):
    """Test that list_tables works with specific schema parameter"""
    result = await list_tables(db_manager, "chinook_sqlite", schema="main")

    assert isinstance(result, TablesResponse)
    assert len(result.schemas) == 1
    assert result.schemas[0].db_schema == "main"
    assert len(result.schemas[0].tables) > 0
    assert result.schemas[0].table_count == len(result.schemas[0].tables)


async def test_list_tables_nonexistent_schema(db_manager):
    """Test that list_tables handles non-existent schema gracefully"""
    with pytest.raises(ListTablesError):
        await list_tables(db_manager, "chinook_sqlite", schema="nonexistent_schema")
