"""Unit tests for describe_table function"""

import os
import pytest

from database_manager import load_config, DatabaseManager
from tools.describe_table import describe_table, TableDescription, ErrorResponse


@pytest.fixture
def db_manager():
    config_path = os.path.join(os.path.dirname(__file__), 'test_config.yaml')
    config = load_config(config_path)
    return DatabaseManager(config)


def test_describe_table_album_structure(db_manager):
    """Test that describe_table correctly describes Album table structure"""
    result = describe_table(db_manager, "chinook_sqlite", "Album")

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


def test_describe_table_artist_incoming_fks(db_manager):
    """Test that describe_table correctly finds incoming foreign keys for Artist table"""
    result = describe_table(db_manager, "chinook_sqlite", "Artist")

    assert isinstance(result, TableDescription)
    assert result.table == "Artist"

    assert len(result.incoming_foreign_keys) >= 1

    album_fk = next(
        (fk for fk in result.incoming_foreign_keys if fk.from_table == "Album"), None)
    assert album_fk is not None
    assert album_fk.from_columns == ["ArtistId"]
    assert album_fk.to_columns == ["ArtistId"]


def test_describe_table_customer_multiple_incoming_fks(db_manager):
    """Test that describe_table finds multiple incoming foreign keys for Customer table"""
    result = describe_table(db_manager, "chinook_sqlite", "Customer")

    assert isinstance(result, TableDescription)
    assert result.table == "Customer"

    assert len(result.incoming_foreign_keys) >= 1

    invoice_fk = next(
        (fk for fk in result.incoming_foreign_keys if fk.from_table == "Invoice"), None)
    assert invoice_fk is not None
    assert invoice_fk.from_columns == ["CustomerId"]
    assert invoice_fk.to_columns == ["CustomerId"]


def test_describe_table_nonexistent_table(db_manager):
    """Test that describe_table handles non-existent table gracefully"""
    result = describe_table(db_manager, "chinook_sqlite", "NonexistentTable")

    assert isinstance(result, ErrorResponse)
    assert "Table description failed" in result.error


def test_describe_table_nonexistent_database(db_manager):
    """Test that describe_table handles non-existent database name"""
    result = describe_table(db_manager, "nonexistent_db", "Album")

    assert isinstance(result, ErrorResponse)
    assert "Database 'nonexistent_db' not found" in result.error


def test_describe_table_connection_error(db_manager):
    """Test that describe_table errors when trying to connect to non-connectable DB"""
    result = describe_table(db_manager, "test_postgres", "some_table")

    assert isinstance(result, ErrorResponse)
    assert "Table description failed" in result.error


def test_describe_table_column_types_and_nullability(db_manager):
    """Test that describe_table correctly reports column types and nullability"""
    result = describe_table(db_manager, "chinook_sqlite", "Track")

    assert isinstance(result, TableDescription)

    track_id_col = next(
        (col for col in result.columns if col.name == "TrackId"), None)
    name_col = next(
        (col for col in result.columns if col.name == "Name"), None)

    assert track_id_col is not None
    assert name_col is not None

    assert track_id_col.primary_key is True
    assert track_id_col.nullable is False
    assert name_col.nullable is False

    assert isinstance(track_id_col.type, str)
    assert isinstance(name_col.type, str)
