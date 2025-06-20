# app/services/requests/fetch.py

import logging
import polars as pl
from connectorx import read_sql
import sqlite3 # Required for local SQLite database operations
from typing import Union, Dict, Any
from urllib.parse import quote_plus # Used for URL-encoding driver names

# Local imports from project schemas
from app.core.schemas.input_schema import ExternalDBSchema, LocalDBSchema

# Initialize logger for this module
logger = logging.getLogger(__name__)

def _build_external_db_connection_string(db_config: ExternalDBSchema) -> str:
    """
    Builds a database connection string compatible with ConnectorX for an external database.
    This function handles securely retrieving the password from SecretStr and
    optionally adds an ODBC driver specification for MSSQL connections.

    Args:
        db_config (ExternalDBSchema): A Pydantic model containing external database connection details.
                                      This includes db_type, username, password, host, port, db_name, sql_query, and an optional driver.

    Returns:
        str: The formatted connection string ready for use with ConnectorX.
    """
    # Safely retrieve the raw password value from the SecretStr object.
    # If db_config.password is None or an empty SecretStr, this will result in an empty string.
    password = db_config.password.get_secret_value() if db_config.password else ""
    
    # A masked version of the password for logging/debugging to avoid exposing sensitive info in console.
    masked_password_display = "*****"
    
    # Construct the base connection string. ConnectorX uses a URL-like format.
    # Example: postgresql://user:pass@host:port/dbname
    conn_str = f"{db_config.db_type}://{db_config.username}:{password}@{db_config.host}:{db_config.port}/{db_config.db_name}"

    # Special handling for MSSQL connections: add the ODBC driver parameter if provided.
    # The driver name often contains spaces (e.g., "ODBC Driver 17 for SQL Server"),
    # so it needs to be URL-encoded for the connection string.
    if db_config.driver and db_config.db_type.lower() == 'mssql':
        encoded_driver = quote_plus(db_config.driver) # URL-encode the driver name
        conn_str += f"?driver={encoded_driver}" # Append the driver parameter
        logger.debug(f"Added ODBC driver parameter to MSSQL connection string: '{db_config.driver}'.")
    elif db_config.driver:
        # Log a warning if a driver is provided for a database type that typically doesn't need it
        # or where ConnectorX might ignore it.
        logger.warning(f"Driver '{db_config.driver}' provided for non-MSSQL database type '{db_config.db_type}'. "
                       "This parameter might be ignored by ConnectorX for this database type.")

    # --- CRITICAL DEBUG LINE: Log the final constructed connection string (with password masked). ---
    # This is invaluable for debugging "Login failed" errors by confirming what's being sent to the DB.
    # It will appear in your FastAPI console output.
    final_log_conn_str = conn_str.replace(password, masked_password_display) if password else conn_str
    logger.info(f"DEBUG: Final ConnectorX connection string (password masked for console): {final_log_conn_str}")

    return conn_str

def _fetch_from_external_db(db_config: ExternalDBSchema) -> pl.LazyFrame:
    """
    Fetches data from an external relational database using the provided configuration
    and returns it as a Polars LazyFrame.

    Args:
        db_config (ExternalDBSchema): A Pydantic model containing all necessary details
                                      for connecting to an external database and the SQL query to execute.

    Returns:
        pl.LazyFrame: A lazy representation of the query result. This allows Polars to optimize
                      operations and potentially handle datasets larger than memory.

    Raises:
        ValueError: If the `sql_query` field in `db_config` is empty or missing.
        RuntimeError: If any error occurs during the database connection or data fetching process
                      (e.g., incorrect credentials, network issues, database server errors, invalid query).
    """
    if not db_config.sql_query:
        raise ValueError("ExternalDBSchema object must contain a non-empty 'sql_query' to fetch data.")

    # Build the full connection string using the helper function
    conn_str = _build_external_db_connection_string(db_config)
    query = db_config.sql_query

    logger.info(f"Attempting to fetch data from external DB '{db_config.db_type}' at '{db_config.host}:{db_config.port}/{db_config.db_name}'.")
    logger.debug(f"Executing external SQL query: '{query[:150]}...' (truncated for log verbosity if long)") # Log truncated query

    try:
        # Use ConnectorX's read_sql function to fetch data.
        # ConnectorX is optimized for high-performance data transfer from databases.
        df = read_sql(conn_str, query)

        # ConnectorX typically returns a Polars DataFrame if Polars is installed.
        # However, as a safeguard, convert to Polars DataFrame explicitly if it's not already.
        if not isinstance(df, pl.DataFrame):
            logger.warning(f"ConnectorX returned data as {type(df).__name__}, converting to Polars DataFrame.")
            df = pl.DataFrame(df)

        logger.info(f"Successfully retrieved {df.shape[0]} rows and {df.shape[1]} columns from external DB.")
        return df.lazy() # Return a LazyFrame for efficient downstream processing
    except Exception as e:
        # Log the error with detailed context, including the masked connection string
        masked_conn_str_for_error = conn_str.replace(db_config.password.get_secret_value(), '*****') if db_config.password else conn_str
        logger.error(f"Failed to fetch data from external DB. Connection String: '{masked_conn_str_for_error}'. Error: {e}", exc_info=True)
        raise RuntimeError(f"External database fetch failed: {e}. Please check your connection details, credentials, and SQL query.") from e

def _fetch_from_local_db(db_config: LocalDBSchema) -> pl.LazyFrame:
    """
    Fetches data from a local SQLite database (file-based or in-memory).
    This function handles connecting to SQLite, optionally executing initial SQL commands,
    and then performing the main data query.

    Args:
        db_config (LocalDBSchema): A Pydantic model containing configuration for the local SQLite database,
                                   including file path, optional initial SQL, and the main SQL query.

    Returns:
        pl.LazyFrame: A lazy representation of the query result from the SQLite database.

    Raises:
        ValueError: If the `sql_query` field in `db_config` is empty or missing.
        RuntimeError: If any error occurs during SQLite database operations (e.g., connection,
                      initial SQL script execution, main query execution).
    """
    if not db_config.sql_query:
        raise ValueError("LocalDBSchema object must contain a non-empty 'sql_query' to fetch data.")

    db_path = db_config.db_file_path
    logger.info(f"Attempting to connect to local SQLite DB at path: '{db_path}'.")

    conn = None # Initialize connection object to None; essential for finally block cleanup
    try:
        conn = sqlite3.connect(db_path) # Establish connection to SQLite database
        cursor = conn.cursor() # Create a cursor object to execute SQL commands

        # If initial SQL commands are provided, execute them. This is often used for
        # creating tables or populating initial data in a new or in-memory database.
        if db_config.initial_sql:
            logger.debug(f"Executing initial SQL for local DB: '{db_config.initial_sql[:150]}...' (truncated)")
            cursor.executescript(db_config.initial_sql) # Executes multiple SQL statements separated by semicolons
            conn.commit() # Commit changes made by initial SQL (e.g., CREATE TABLE, INSERT)
            logger.info("Initial SQL executed successfully for local DB.")

        # Execute the main SQL query to fetch data
        logger.debug(f"Executing main local SQL query: '{db_config.sql_query[:150]}...' (truncated)")
        cursor.execute(db_config.sql_query)
        rows = cursor.fetchall() # Fetch all resulting rows from the executed query
        
        # Extract column names from the cursor's description attribute, which holds metadata about the result set.
        column_names = [description[0] for description in cursor.description]

        # Create a Polars DataFrame from the fetched rows and column names.
        df = pl.DataFrame(rows, schema=column_names)
        logger.info(f"Retrieved {df.shape[0]} rows and {df.shape[1]} columns from local SQLite DB.")

        return df.lazy() # Return a LazyFrame for efficient, optimized processing

    except sqlite3.Error as e:
        # Catch specific SQLite errors for precise error reporting
        logger.error(f"SQLite database error during fetch from '{db_path}': {e}", exc_info=True)
        raise RuntimeError(f"Local SQLite database operation failed: {e}. Please check your DB file path and SQL query syntax.") from e
    except Exception as e:
        # Catch any other unexpected errors during the local DB fetch process
        logger.error(f"An unexpected error occurred during local DB fetch from '{db_path}': {e}", exc_info=True)
        raise RuntimeError(f"Local database fetch failed: {e}. An unexpected error occurred.") from e
    finally:
        # Ensure the SQLite connection is always closed to prevent resource leaks.
        if conn:
            conn.close()
            logger.debug(f"Closed connection to local SQLite DB: '{db_path}'.")

def fetch_data(db_config: Union[ExternalDBSchema, LocalDBSchema]) -> pl.LazyFrame:
    """
    Main entry point for data fetching. This function acts as a dispatcher,
    routing the request to the appropriate internal fetching function based on
    the type of database configuration provided (external or local SQLite).

    Args:
        db_config (Union[ExternalDBSchema, LocalDBSchema]): The database configuration object.
                                                            This object determines which database
                                                            fetching logic will be applied.

    Returns:
        pl.LazyFrame: A Polars LazyFrame containing the fetched data.

    Raises:
        ValueError: If an unsupported `db_config` type is provided, which should ideally
                    be caught by Pydantic validation upstream in API endpoints.
        RuntimeError: Propagates runtime errors from the specific fetching functions
                      (`_fetch_from_external_db` or `_fetch_from_local_db`).
    """
    if isinstance(db_config, ExternalDBSchema):
        logger.info(f"Dispatching fetch request to external database handler (type: {db_config.db_type}).")
        return _fetch_from_external_db(db_config)
    elif isinstance(db_config, LocalDBSchema):
        logger.info(f"Dispatching fetch request to local SQLite database handler (path: {db_config.db_file_path}).")
        return _fetch_from_local_db(db_config)
    else:
        # This case acts as a defensive programming measure. If the input `db_config`
        # is neither an ExternalDBSchema nor a LocalDBSchema, it indicates a type mismatch.
        logger.error(f"Received unsupported database configuration type: {type(db_config).__name__}. Expected ExternalDBSchema or LocalDBSchema.")
        raise ValueError(f"Unsupported database configuration type provided: {type(db_config).__name__}. "
                         "Please provide either an ExternalDBSchema or a LocalDBSchema object.")
