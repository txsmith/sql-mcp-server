import os
import pytest

from database_manager import load_config, DatabaseManager
from tools.sample_table import sample_table, SampleResponse, SampleTableError


@pytest.fixture
async def db_manager():
    """Fixture to provide database manager for tests"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "test_config.yaml")
    config = load_config(config_path)
    return DatabaseManager(config)


async def test_sample_table_album_default_limit(db_manager):
    """Test that sample_table returns sample data from Album table with default limit"""
    result = await sample_table(db_manager, "chinook_sqlite", "Album")

    assert isinstance(result, SampleResponse)
    assert result.table == "Album"
    assert len(result.columns) == 3

    expected_columns = ["AlbumId", "Title", "ArtistId"]
    for col in expected_columns:
        assert col in result.columns

    assert len(result.rows) == result.row_count
    assert result.row_count <= 10  # Default sample size


async def test_sample_table_with_custom_limit(db_manager):
    """Test that sample_table respects custom limit parameter"""
    limit = 5
    result = await sample_table(db_manager, "chinook_sqlite", "Track", limit)

    assert isinstance(result, SampleResponse)
    assert result.table == "Track"
    assert result.row_count == limit
    assert len(result.rows) == limit


async def test_sample_table_nonexistent_table(db_manager):
    """Test that sample_table handles non-existent table"""
    with pytest.raises(SampleTableError):
        await sample_table(db_manager, "chinook_sqlite", "NonexistentTable")


async def test_sample_table_data_structure(db_manager):
    """Test that sample_table returns proper data structure"""
    result = await sample_table(db_manager, "chinook_sqlite", "Artist", limit=3)

    assert isinstance(result, SampleResponse)

    assert isinstance(result.rows, list)
    if result.rows:
        assert isinstance(result.rows[0], dict)

        for row in result.rows:
            assert set(row.keys()) == set(result.columns)


async def test_sample_table_large_limit(db_manager):
    """Test that sample_table handles limits larger than table size"""
    result = await sample_table(db_manager, "chinook_sqlite", "Album", limit=1000)

    assert isinstance(result, SampleResponse)
    assert result.row_count <= 1000


async def test_sample_table_employee_structure(db_manager):
    """Test that sample_table correctly samples Employee table structure"""
    result = await sample_table(db_manager, "chinook_sqlite", "Employee", limit=2)

    assert isinstance(result, SampleResponse)
    assert result.table == "Employee"
    assert result.row_count <= 2

    expected_columns = [
        "EmployeeId",
        "LastName",
        "FirstName",
        "Title",
        "ReportsTo",
        "BirthDate",
        "HireDate",
        "Address",
        "City",
        "State",
        "Country",
        "PostalCode",
        "Phone",
        "Fax",
        "Email",
    ]

    for col in expected_columns:
        assert col in result.columns
