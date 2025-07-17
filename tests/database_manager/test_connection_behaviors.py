import os
import pytest

from database_manager import (
    load_config,
    DatabaseManager,
    ConnectionError,
    DatabaseNotFoundError,
)


@pytest.fixture
def db_manager():
    """Fixture to provide database manager for tests"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "test_config.yaml")
    config = load_config(config_path)
    return DatabaseManager(config)


class TestConnectionErrors:
    """Test suite for connection error scenarios via database_manager.connect()"""

    async def test_connection_error_unreachable_database(self, db_manager):
        """Test that connect() raises ConnectionError for unreachable databases"""
        with pytest.raises(
            ConnectionError, match="Failed to connect to database 'test_postgres'"
        ):
            async with db_manager.connect("test_postgres") as conn:
                pass


class TestDatabaseNotFoundErrors:
    """Test suite for database not found error scenarios via database_manager"""

    async def test_database_not_found_error_nonexistent_database(self, db_manager):
        """Test that connect() raises DatabaseNotFoundError for nonexistent databases"""
        with pytest.raises(DatabaseNotFoundError):
            async with db_manager.connect("nonexistent_db") as conn:
                pass


class TestConnectionContextManager:
    """Test suite for connection context manager behavior"""

    async def test_connection_context_manager_cleanup_on_success(self, db_manager):
        """Test that connection context manager properly cleans up on successful exit"""
        conn_ref = None
        async with db_manager.connect("chinook_sqlite") as conn:
            conn_ref = conn
            assert conn is not None

        assert conn_ref.closed

    async def test_connection_context_manager_cleanup_on_exception(self, db_manager):
        """Test that connection context manager properly cleans up on exception"""
        conn_ref = None
        with pytest.raises(RuntimeError):
            async with db_manager.connect("chinook_sqlite") as conn:
                conn_ref = conn
                assert conn is not None
                raise RuntimeError("Test exception")

        assert conn_ref.closed
