import os
import pytest

from database_manager import (
    load_config,
    DatabaseManager,
)
from tools.describe_table import (
    describe_table,
    TableDescription,
    TableNotFoundError,
)


@pytest.fixture
def db_manager():
    config_path = os.path.join(os.path.dirname(__file__), "../test_config.yaml")
    config = load_config(config_path)
    return DatabaseManager(config)


async def test_describe_table_album_structure(db_manager):
    """Test that describe_table correctly describes Album table structure"""
    result = await describe_table(db_manager, "chinook_sqlite", "Album")

    assert isinstance(result, TableDescription)
    assert result.table == "Album"

    assert len(result.columns) == 3

    column_names = [col.name for col in result.columns]
    expected_columns = ["AlbumId", "Title", "ArtistId"]
    for expected_col in expected_columns:
        assert expected_col in column_names

    album_id_col = next(col for col in result.columns if col.name == "AlbumId")
    assert album_id_col.primary_key is True
    assert album_id_col.nullable is False

    assert len(result.foreign_keys) == 1
    fk = result.foreign_keys[0]
    assert fk.constrained_columns == ["ArtistId"]
    assert fk.referred_table == "Artist"
    assert fk.referred_columns == ["ArtistId"]


async def test_describe_table_artist_incoming_fks(db_manager):
    """Test that describe_table correctly finds incoming foreign keys for Artist table"""
    result = await describe_table(db_manager, "chinook_sqlite", "Artist")

    assert isinstance(result, TableDescription)
    assert result.table == "Artist"

    assert len(result.incoming_foreign_keys) >= 1

    album_fk = next(
        (fk for fk in result.incoming_foreign_keys if fk.from_table == "Album"), None
    )
    assert album_fk is not None
    assert album_fk.from_columns == ["ArtistId"]
    assert album_fk.to_columns == ["ArtistId"]


async def test_describe_table_customer_multiple_incoming_fks(db_manager):
    """Test that describe_table finds multiple incoming foreign keys for Customer table"""
    result = await describe_table(db_manager, "chinook_sqlite", "Customer")

    assert isinstance(result, TableDescription)
    assert result.table == "Customer"

    assert len(result.incoming_foreign_keys) >= 1

    invoice_fk = next(
        (fk for fk in result.incoming_foreign_keys if fk.from_table == "Invoice"), None
    )
    assert invoice_fk is not None
    assert invoice_fk.from_columns == ["CustomerId"]
    assert invoice_fk.to_columns == ["CustomerId"]


async def test_describe_table_nonexistent_table(db_manager):
    """Test that describe_table handles non-existent table gracefully"""
    with pytest.raises(TableNotFoundError):
        await describe_table(db_manager, "chinook_sqlite", "NonexistentTable")


async def test_describe_table_column_types_and_nullability(db_manager):
    """Test that describe_table correctly reports column types and nullability"""
    result = await describe_table(db_manager, "chinook_sqlite", "Track")

    assert isinstance(result, TableDescription)

    track_id_col = next((col for col in result.columns if col.name == "TrackId"), None)
    name_col = next((col for col in result.columns if col.name == "Name"), None)

    assert track_id_col is not None
    assert name_col is not None

    assert track_id_col.primary_key is True
    assert track_id_col.nullable is False
    assert name_col.nullable is False

    assert isinstance(track_id_col.type, str)
    assert isinstance(name_col.type, str)


async def test_describe_table_pagination_fields(db_manager):
    """Test that describe_table returns pagination fields correctly"""
    result = await describe_table(
        db_manager, "chinook_sqlite", "Track", limit=5, page=1
    )

    assert isinstance(result, TableDescription)
    assert result.current_page == 1
    assert result.total_count > 0
    assert result.total_pages > 0
    assert len(result.columns) <= 5


async def test_describe_table_pagination_limit_validation(db_manager):
    """Test that describe_table validates pagination parameters"""
    from tools.describe_table import DescribeTableError

    with pytest.raises(DescribeTableError, match="Limit must be greater than 0"):
        await describe_table(db_manager, "chinook_sqlite", "Track", limit=0)

    with pytest.raises(DescribeTableError, match="Page number must be greater than 0"):
        await describe_table(db_manager, "chinook_sqlite", "Track", page=0)


async def test_describe_table_pagination_second_page(db_manager):
    """Test that describe_table pagination works for second page"""
    result_page1 = await describe_table(
        db_manager, "chinook_sqlite", "Track", limit=3, page=1
    )
    result_page2 = await describe_table(
        db_manager, "chinook_sqlite", "Track", limit=3, page=2
    )

    assert result_page1.current_page == 1
    assert result_page2.current_page == 2
    assert result_page1.total_count == result_page2.total_count
    assert result_page1.total_pages == result_page2.total_pages

    # Make sure we get different items (at least some should be different)
    page1_items = [col.name for col in result_page1.columns] + [
        fk.referred_table for fk in result_page1.foreign_keys
    ]
    page2_items = [col.name for col in result_page2.columns] + [
        fk.referred_table for fk in result_page2.foreign_keys
    ]

    # Pages should be different
    if result_page1.total_count > 3:
        assert page1_items != page2_items
