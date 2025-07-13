"""Shared database manager for MCP tools"""

import yaml
from typing import Dict, Any, List
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL
from pydantic import BaseModel, model_validator
from password_provider import PasswordProvider, PassPasswordProvider


class DatabaseConfig(BaseModel):
    type: str
    description: str

    # Option 1: Use connection string directly
    connection_string: str | None = None

    # Option 2: Use individual fields
    host: str | None = None
    port: int | None = None
    database: str | None = None
    username: str | None = None
    password: str | None = None
    account: str | None = None  # For Snowflake

    # Custom password store key (overrides default databases/{db_name})
    password_store_key: str | None = None

    extra_params: Dict[str, str] | None = None

    @model_validator(mode="after")
    def validate_config(self):
        # Validate supported database types
        supported_types = {"postgresql", "mysql", "sqlserver", "snowflake", "sqlite"}
        if self.type not in supported_types:
            raise ValueError(f"Unsupported database type: {self.type}")

        # If using connection string, no further validation needed
        if self.connection_string:
            return self

        if not self.database:
            raise ValueError("database field is required")

        # For SQLite, only database field is required
        if self.type == "sqlite":
            return self

        if not all([self.host, self.database, self.username]):
            raise ValueError(
                "Either connection_string or host/database/username must be provided"
            )

        return self

    @property
    def dialect(self) -> str:
        dialect_map = {
            "postgresql": "postgresql",
            "mysql": "mysql+pymysql",
            "sqlserver": "mssql+pyodbc",
            "snowflake": "snowflake",
            "sqlite": "sqlite",
        }
        return dialect_map[self.type]


class AppConfig(BaseModel):
    databases: Dict[str, DatabaseConfig]
    settings: Dict[str, Any]

    @model_validator(mode="after")
    def validate_config(self):
        seen_names = set()
        for db_name in self.databases.keys():
            name_lower = db_name.lower()
            if name_lower in seen_names:
                raise ValueError(f"{db_name} is defined twice!")
            seen_names.add(name_lower)

        return self


class DatabaseManager:
    def __init__(
        self, config: AppConfig, password_provider: PasswordProvider | None = None
    ):
        self.config = config
        self.password_provider = password_provider or PassPasswordProvider()
        self.engines: Dict[str, Engine] = {}

    def get_connection_url(self, label: str, db_config: DatabaseConfig):
        if db_config.connection_string:
            return db_config.connection_string

        if db_config.type == "sqlite":
            if db_config.database == ":memory:":
                return "sqlite:///:memory:"
            else:
                return f"sqlite:///{db_config.database}"

        # Try to get password from provider if not configured
        password = db_config.password
        if not password and db_config.username:
            pass_key = db_config.password_store_key or f"databases/{label}"
            password = self.password_provider.get_password(pass_key)

        # Special handling for Snowflake account parameter
        query_params = db_config.extra_params.copy() if db_config.extra_params else {}
        if db_config.type == "snowflake" and db_config.account:
            query_params["account"] = db_config.account

        url = URL.create(
            drivername=db_config.dialect,
            username=db_config.username,
            password=password,
            host=db_config.host,
            port=db_config.port,
            database=db_config.database,
            query=query_params,
        )

        return url

    def get_engine(self, db_label: str) -> Engine | None:
        if db_label not in self.engines:
            db_config = self.config.databases.get(db_label)
            if not db_config:
                return None

            try:
                engine_kwargs = {"echo": False}
                url = self.get_connection_url(db_label, db_config)

                # Only add pool_timeout for non-SQLite databases
                if not str(url).startswith("sqlite"):
                    engine_kwargs["pool_timeout"] = self.config.settings.get(
                        "max_query_timeout", 30
                    )

                engine = create_engine(url, **engine_kwargs)
                self.engines[db_label] = engine
            except Exception as e:
                print(f"Failed to initialize engine for {db_label}: {e}")
                return None

        return self.engines.get(db_label)

    def list_database_names(self) -> List[str]:
        return list(self.config.databases.keys())

    def get_database_config(self, db_name: str) -> DatabaseConfig | None:
        return self.config.databases.get(db_name)


def load_config(config_path: str) -> AppConfig:
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)
    return AppConfig(**config_data)
