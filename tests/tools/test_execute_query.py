import os
import pytest

from database_manager import (
    load_config,
    DatabaseManager,
    QueryError,
)
from tools.execute_query import execute_query, QueryResponse


@pytest.fixture
async def db_manager():
    """Fixture to provide database manager for tests"""
    config_path = os.path.join(os.path.dirname(__file__), "../test_config.yaml")
    config = load_config(config_path)
    return DatabaseManager(config)


async def test_execute_query_simple_select(db_manager):
    """Test that execute_query works with a simple SELECT query"""
    query = "SELECT AlbumId, Title FROM Album LIMIT 3"
    result = await execute_query(db_manager, "chinook_sqlite", query)

    assert isinstance(result, QueryResponse)
    assert len(result.columns) == 2
    assert "AlbumId" in result.columns
    assert "Title" in result.columns
    assert result.row_count == 3
    assert len(result.rows) == 3
    assert not result.truncated


async def test_execute_query_invalid_sql(db_manager):
    """Test that execute_query handles invalid SQL"""
    query = "SELECT * FROM NonexistentTable"
    with pytest.raises(QueryError):
        await execute_query(db_manager, "chinook_sqlite", query)


async def test_execute_query_join_query(db_manager):
    """Test that execute_query works with JOIN queries"""
    query = """
    SELECT a.Title, ar.Name as ArtistName
    FROM Album a
    JOIN Artist ar ON a.ArtistId = ar.ArtistId
    LIMIT 5
    """
    result = await execute_query(db_manager, "chinook_sqlite", query)

    assert isinstance(result, QueryResponse)
    assert len(result.columns) == 2
    assert "Title" in result.columns
    assert "ArtistName" in result.columns
    assert result.row_count == 5


async def test_execute_query_aggregate_functions(db_manager):
    """Test that execute_query works with aggregate functions"""
    query = "SELECT COUNT(*) as total_albums FROM Album"
    result = await execute_query(db_manager, "chinook_sqlite", query)

    assert isinstance(result, QueryResponse)
    assert len(result.columns) == 1
    assert "total_albums" in result.columns
    assert result.row_count == 1
    assert result.rows[0]["total_albums"] > 0


async def test_execute_query_truncation_behavior(db_manager):
    """Test that execute_query properly handles row limits and truncation"""
    # This test assumes Chinook has more than 10 tracks
    query = "SELECT TrackId FROM Track"
    result = await execute_query(db_manager, "chinook_sqlite", query)

    assert isinstance(result, QueryResponse)
    # Should be truncated to max_rows_per_query (500 in test config)
    assert result.row_count <= 500

    # If there are more than 500 tracks, it should be truncated
    if result.row_count == 500:
        assert result.truncated
    else:
        assert not result.truncated


async def test_execute_query_empty_result_set(db_manager):
    """Test that execute_query handles queries that return no rows"""
    query = "SELECT * FROM Album WHERE AlbumId = -1"
    result = await execute_query(db_manager, "chinook_sqlite", query)

    assert isinstance(result, QueryResponse)
    assert result.row_count == 0
    assert len(result.rows) == 0
    assert not result.truncated


async def test_execute_query_data_types(db_manager):
    """Test that execute_query handles different data types correctly"""
    query = """
    SELECT
        EmployeeId,
        FirstName,
        BirthDate,
        ReportsTo
    FROM Employee
    LIMIT 1
    """
    result = await execute_query(db_manager, "chinook_sqlite", query)

    assert isinstance(result, QueryResponse)
    assert result.row_count == 1

    row = result.rows[0]
    assert isinstance(row["EmployeeId"], int)
    assert isinstance(row["FirstName"], str)
    # BirthDate and ReportsTo can be None or have values


async def test_execute_query_with_comments(db_manager):
    """Test that execute_query works with SQL comments"""
    query = """
    /* This is a comment */
    SELECT AlbumId, Title
    FROM Album
    -- Another comment
    LIMIT 2
    """
    result = await execute_query(db_manager, "chinook_sqlite", query)

    assert isinstance(result, QueryResponse)
    assert result.row_count == 2
