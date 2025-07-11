"""Shared database manager for MCP tools"""

import yaml
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL
from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    type: str
    description: str

    # Option 1: Use connection string directly
    connection_string: Optional[str] = None

    # Option 2: Use individual fields
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    account: Optional[str] = None  # For Snowflake

    extra_params: Optional[Dict[str, str]] = None

    def get_connection_url(self):
        """Get SQLAlchemy URL from config"""
        if self.connection_string:
            return self.connection_string

        if self.type == "sqlite":
            if not self.database:
                raise ValueError("SQLite requires database field")
            if self.database == ":memory:":
                return "sqlite:///:memory:"
            else:
                return f"sqlite:///{self.database}"

        if not all([self.host, self.database, self.username]):
            raise ValueError(
                "Either connection_string or host/database/username must be provided"
            )

        dialect_map = {
            "postgresql": "postgresql",
            "mysql": "mysql+pymysql",
            "sqlserver": "mssql+pyodbc",
            "snowflake": "snowflake",
        }

        dialect = dialect_map.get(self.type)
        if not dialect:
            raise ValueError(f"Unsupported database type: {self.type}")

        # Special handling for Snowflake account parameter
        query_params = self.extra_params.copy() if self.extra_params else {}
        if self.type == "snowflake" and self.account:
            query_params["account"] = self.account

        url = URL.create(
            drivername=dialect,
            username=self.username,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
            query=query_params,
        )

        return url


class AppConfig(BaseModel):
    databases: Dict[str, DatabaseConfig]
    settings: Dict[str, Any]


class DatabaseManager:
    def __init__(self, config: AppConfig):
        self.config = config
        self.engines: Dict[str, Engine] = {}
        self._initialize_engines()

    def _initialize_engines(self):
        for db_name, db_config in self.config.databases.items():
            try:
                engine_kwargs = {"echo": False}
                url = db_config.get_connection_url()

                # Only add pool_timeout for non-SQLite databases
                if not str(url).startswith("sqlite"):
                    engine_kwargs["pool_timeout"] = self.config.settings.get(
                        "max_query_timeout", 30
                    )

                engine = create_engine(url, **engine_kwargs)
                self.engines[db_name] = engine
            except Exception as e:
                print(f"Failed to initialize engine for {db_name}: {e}")

    def get_engine(self, db_name: str) -> Optional[Engine]:
        return self.engines.get(db_name)

    def list_database_names(self) -> List[str]:
        return list(self.engines.keys())

    def get_database_config(self, db_name: str) -> Optional[DatabaseConfig]:
        return self.config.databases.get(db_name)


def load_config(config_path: str) -> AppConfig:
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)
    return AppConfig(**config_data)
