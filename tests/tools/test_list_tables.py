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
    result = await list_tables(db_manager, "chinook_sqlite", limit=10, page=1)

    assert isinstance(result, TablesResponse)
    assert result.database == "chinook_sqlite"
    assert result.total_count >= 0
    assert result.current_page == 1
    assert result.total_pages >= 1


async def test_list_tables_chinook_database(db_manager):
    """Test that list_tables can find tables in Chinook database"""
    result = await list_tables(db_manager, "chinook_sqlite", limit=100, page=1)

    assert isinstance(result, TablesResponse)
    assert len(result.schemas) > 0

    all_tables = []
    for schema in result.schemas:
        all_tables.extend(schema.tables)

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
    result = await list_tables(db_manager, "test_sqlite", limit=10, page=1)

    assert isinstance(result, TablesResponse)
    assert len(result.schemas) == 0
    assert result.total_count == 0
    assert result.current_page == 1
    assert result.total_pages == 1


async def test_list_tables_with_specific_schema(db_manager):
    """Test that list_tables works with specific schema parameter"""
    result = await list_tables(
        db_manager, "chinook_sqlite", limit=10, page=1, schema="main"
    )

    assert isinstance(result, TablesResponse)
    assert len(result.schemas) == 1
    assert result.schemas[0].db_schema == "main"
    assert len(result.schemas[0].tables) > 0


async def test_list_tables_pagination(db_manager):
    """Test that pagination works correctly"""
    # Get first page with small limit
    page1 = await list_tables(db_manager, "chinook_sqlite", limit=5, page=1)
    assert page1.current_page == 1
    assert page1.total_count == 11
    assert page1.total_pages == 3
    assert len([t for s in page1.schemas for t in s.tables]) == 5

    # Get second page
    page2 = await list_tables(db_manager, "chinook_sqlite", limit=5, page=2)
    assert page2.current_page == 2
    assert page2.total_count == 11
    assert page2.total_pages == 3
    assert len([t for s in page2.schemas for t in s.tables]) == 5

    # Get third page (should have 1 table)
    page3 = await list_tables(db_manager, "chinook_sqlite", limit=5, page=3)
    assert page3.current_page == 3
    assert page3.total_count == 11
    assert page3.total_pages == 3
    assert len([t for s in page3.schemas for t in s.tables]) == 1

    # Pages should have different tables
    page1_tables = [t for s in page1.schemas for t in s.tables]
    page2_tables = [t for s in page2.schemas for t in s.tables]
    assert set(page1_tables).isdisjoint(set(page2_tables))


async def test_list_tables_invalid_page_number(db_manager):
    """Test that invalid page numbers raise errors"""
    with pytest.raises(ListTablesError, match="Page number must be greater than 0"):
        await list_tables(db_manager, "chinook_sqlite", limit=10, page=0)

    with pytest.raises(ListTablesError, match="Page number must be greater than 0"):
        await list_tables(db_manager, "chinook_sqlite", limit=10, page=-1)


async def test_list_tables_invalid_limit(db_manager):
    """Test that invalid limit values raise errors"""
    with pytest.raises(ListTablesError, match="Limit must be greater than 0"):
        await list_tables(db_manager, "chinook_sqlite", limit=0, page=1)

    with pytest.raises(ListTablesError, match="Limit must be greater than 0"):
        await list_tables(db_manager, "chinook_sqlite", limit=-1, page=1)


async def test_list_tables_limit_clamping():
    """Test that limit is clamped to max_rows_per_query"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "test_config.yaml")
    config = load_config(config_path)

    # Set very low max_rows_per_query
    config.settings["max_rows_per_query"] = 3

    db_manager = DatabaseManager(config)

    result = await list_tables(db_manager, "chinook_sqlite", limit=10, page=1)
    assert isinstance(result, TablesResponse)

    total_tables_returned = len([t for s in result.schemas for t in s.tables])
    assert total_tables_returned == 3
