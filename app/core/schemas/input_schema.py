# app/core/schemas/input_schema.py

import logging
from typing import Optional, List, Union
from pydantic import BaseModel, Field, SecretStr # SecretStr for sensitive data

logger = logging.getLogger(__name__)

class Input(BaseModel):
    """
    Represents an input configuration for column transformations in a DataFrame.
    Used for renaming or reordering columns.
    """
    name: Optional[str] = Field(None, description="New name for the column (for renaming operations). This also serves as a unique identifier for the input configuration.")
    column: Optional[int] = Field(None, description="Zero-based index of the column to target (e.g., 0 for the first column). Required for both renaming and reordering.")
    change_order: Optional[int] = Field(None, description="New zero-based position for the column in the reordered DataFrame. Used for reordering operations.")

class ExternalDBSchema(BaseModel):
    """
    Represents connection details for an external relational database.
    """
    db_type: str = Field(..., description="Type of the database (e.g., 'postgresql', 'mysql', 'sqlserver', 'mssql').")
    username: str = Field(..., description="Username for database authentication.")
    password: SecretStr = Field(..., description="Password for database authentication. Stored as SecretStr for security.")
    host: str = Field(..., description="Database host address.")
    port: str = Field(..., description="Database port number.")
    db_name: str = Field(..., description="Name of the database.")
    sql_query: str = Field(..., description="SQL query to fetch data from the external database.")
    # THIS FIELD IS CRUCIAL:
    driver: Optional[str] = Field(None, description="Optional ODBC driver name for databases like MSSQL (e.g., 'ODBC Driver 17 for SQL Server'). Required for some ConnectorX connections.")


class LocalDBSchema(BaseModel):
    """
    Represents configuration for a local SQLite database (file-based or in-memory).
    """
    db_file_path: str = Field(":memory:", description="Path to the SQLite database file. Use ':memory:' for an in-memory database.")
    initial_sql: Optional[str] = Field(None, description="Optional SQL script to initialize the SQLite database (e.g., CREATE TABLE, INSERT statements). Executed only if the DB file is newly created or ':memory:'.")
    sql_query: str = Field(..., description="SQL query to fetch data from the local SQLite database.")

class Configure(BaseModel):
    """
    Represents general application configuration settings for a specific task or pipeline run.
    This includes output file type, temporary directory override, and crucially, database configurations.
    """
    file_type: Optional[str] = Field("csv", description="Desired output file type (e.g., 'csv', 'json', 'xlsx', 'zip'). Defaults to 'csv' if not specified.")
    tmp_dir: Optional[str] = Field(None, description="Temporary directory path. If provided, this path will override the global TEMP_DIR for output files of this specific task.")
    
    # Nested database configuration: This field can hold either an ExternalDBSchema or a LocalDBSchema.
    # Pydantic will attempt to validate against the types in the order they are listed in Union.
    db_config: Optional[Union[LocalDBSchema, ExternalDBSchema]] = Field(
        None, description="Database configuration details (either for an external relational DB or a local SQLite DB). This is mandatory if data fetching is required."
    )
