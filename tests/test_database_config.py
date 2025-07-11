"""Unit tests for DatabaseConfig and expanded config format"""

import pytest
from sqlalchemy.engine.url import URL

from database_manager import DatabaseConfig


def test_connection_string_mode():
    """Test that connection_string mode works as before"""
    config = DatabaseConfig(
        type="postgresql",
        description="Test DB",
        connection_string="postgresql://user:pass@localhost:5432/mydb",
    )

    url = config.get_connection_url()
    assert url == "postgresql://user:pass@localhost:5432/mydb"


def test_individual_fields_postgresql():
    """Test PostgreSQL with individual fields"""
    config = DatabaseConfig(
        type="postgresql",
        description="Test DB",
        host="localhost",
        port=5432,
        database="mydb",
        username="user",
        password="pass",
    )

    url = config.get_connection_url()
    assert isinstance(url, URL)
    assert url.drivername == "postgresql"
    assert url.username == "user"
    assert url.password == "pass"
    assert url.host == "localhost"
    assert url.port == 5432
    assert url.database == "mydb"


def test_individual_fields_mysql():
    """Test MySQL with individual fields"""
    config = DatabaseConfig(
        type="mysql",
        description="Test DB",
        host="localhost",
        port=3306,
        database="mydb",
        username="user",
        password="pass",
    )

    url = config.get_connection_url()
    assert isinstance(url, URL)
    assert url.drivername == "mysql+pymysql"
    assert url.username == "user"
    assert url.password == "pass"
    assert url.host == "localhost"
    assert url.port == 3306
    assert url.database == "mydb"


def test_individual_fields_sqlite():
    """Test SQLite with individual fields"""
    config = DatabaseConfig(
        type="sqlite", description="Test DB", database="/path/to/db.sqlite"
    )

    url = config.get_connection_url()
    assert url == "sqlite:////path/to/db.sqlite"


def test_sqlite_memory():
    """Test SQLite in-memory database"""
    config = DatabaseConfig(type="sqlite", description="Test DB", database=":memory:")

    url = config.get_connection_url()
    assert url == "sqlite:///:memory:"


def test_no_password():
    """Test config without password"""
    config = DatabaseConfig(
        type="postgresql",
        description="Test DB",
        host="localhost",
        port=5432,
        database="mydb",
        username="user",
    )

    url = config.get_connection_url()
    assert isinstance(url, URL)
    assert url.password is None
    assert url.username == "user"
    assert url.host == "localhost"


def test_no_port():
    """Test config without explicit port"""
    config = DatabaseConfig(
        type="postgresql",
        description="Test DB",
        host="localhost",
        database="mydb",
        username="user",
        password="pass",
    )

    url = config.get_connection_url()
    assert isinstance(url, URL)
    assert url.port is None
    assert url.host == "localhost"
    assert url.username == "user"
    assert url.password == "pass"


def test_extra_params():
    """Test config with extra parameters"""
    config = DatabaseConfig(
        type="postgresql",
        description="Test DB",
        host="localhost",
        database="mydb",
        username="user",
        password="pass",
        extra_params={"sslmode": "require", "connect_timeout": "10"},
    )

    url = config.get_connection_url()
    assert isinstance(url, URL)
    url_str = str(url)
    assert "sslmode=require" in url_str
    assert "connect_timeout=10" in url_str


def test_special_characters_in_password():
    """Test that special characters in password are handled properly"""
    config = DatabaseConfig(
        type="postgresql",
        description="Test DB",
        host="localhost",
        database="mydb",
        username="user",
        password="p@ss!w$rd%",
    )

    url = config.get_connection_url()
    assert isinstance(url, URL)
    # SQLAlchemy URL should properly encode special characters
    assert url.password == "p@ss!w$rd%"


def test_missing_required_fields():
    """Test that missing required fields raise ValueError"""
    with pytest.raises(
        ValueError,
        match="Either connection_string or host/database/username must be provided",
    ):
        config = DatabaseConfig(
            type="postgresql",
            description="Test DB",
            host="localhost",
            # Missing database and username
        )
        config.get_connection_url()


def test_unsupported_database_type():
    """Test that unsupported database types raise ValueError"""
    with pytest.raises(ValueError, match="Unsupported database type"):
        config = DatabaseConfig(
            type="oracle",  # Not supported
            description="Test DB",
            host="localhost",
            database="mydb",
            username="user",
        )
        config.get_connection_url()


def test_snowflake_fields():
    """Test Snowflake with individual fields"""
    config = DatabaseConfig(
        type="snowflake",
        description="Test Snowflake DB",
        host="myaccount.snowflakecomputing.com",
        database="MYDB",
        username="user",
        password="pass",
        extra_params={"warehouse": "COMPUTE_WH", "schema": "PUBLIC"},
    )

    url = config.get_connection_url()
    assert isinstance(url, URL)
    url_str = str(url)
    assert "snowflake://" in url_str
    assert "warehouse=COMPUTE_WH" in url_str
    assert "schema=PUBLIC" in url_str


def test_connection_string_takes_precedence():
    """Test that connection_string takes precedence over individual fields"""
    config = DatabaseConfig(
        type="postgresql",
        description="Test DB",
        connection_string="postgresql://conn_user:conn_pass@conn_host:5432/conn_db",
        # These should be ignored
        host="field_host",
        database="field_db",
        username="field_user",
        password="field_pass",
    )

    url = config.get_connection_url()
    assert url == "postgresql://conn_user:conn_pass@conn_host:5432/conn_db"
