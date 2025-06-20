import logging
import polars as pl
from connectorx import read_sql
import sqlite3
from typing import Union
from urllib.parse import quote_plus

from app.core.schemas.input_schema import ExternalDBSchema, LocalDBSchema

logger = logging.getLogger(__name__)

def _build_external_db_connection_string(db_config: ExternalDBSchema) -> str:
    password = db_config.password.get_secret_value() if db_config.password else ""
    masked_password_display = "*****"
    conn_str = f"{db_config.db_type}://{db_config.username}:{password}@{db_config.host}:{db_config.port}/{db_config.db_name}"
    
    # Check for existing query parameters in the connection string
    has_params = '?' in conn_str
    param_prefix = '&' if has_params else '?'

    # Add driver for MSSQL if specified
    if db_config.driver and db_config.db_type.lower() == 'mssql':
        encoded_driver = quote_plus(db_config.driver)
        conn_str += f"{param_prefix}driver={encoded_driver}"
        param_prefix = '&' # Subsequent params will use '&'
        logger.debug(f"Added ODBC driver parameter to MSSQL connection string: '{db_config.driver}'.")
    elif db_config.driver:
        logger.warning(f"Driver '{db_config.driver}' provided for non-MSSQL DB '{db_config.db_type}', might be ignored by ConnectorX.")

    # Add custom connection parameters if provided
    if db_config.connection_parameters:
        conn_str += f"{param_prefix}{db_config.connection_parameters.lstrip('?&')}" # Ensure only one '?' or '&'
        logger.debug(f"Appended custom connection parameters: '{db_config.connection_parameters}'.")

    final_log_conn_str = conn_str.replace(password, masked_password_display) if password else conn_str
    logger.info(f"DEBUG: Final ConnectorX connection string (password masked): {final_log_conn_str}")
    return conn_str

def _fetch_from_external_db(db_config: ExternalDBSchema, chunk_size: int = 10) -> pl.LazyFrame:
    """
    Fetches data from an external relational database in chunks.
    Adjusts pagination syntax based on database type.

    Args:
        db_config (ExternalDBSchema): Configuration for the external database.
        chunk_size (int): Number of rows to fetch per chunk.

    Returns:
        pl.LazyFrame: A Polars LazyFrame containing the fetched data.

    Raises:
        ValueError: If 'sql_query' is empty.
        RuntimeError: If fetching from the external DB fails or times out.
    """
    if not db_config.sql_query:
        raise ValueError("ExternalDBSchema must have a non-empty 'sql_query'.")

    conn_str = _build_external_db_connection_string(db_config)
    base_query = db_config.sql_query.strip().rstrip(';')

    offset = 0
    dfs = []

    logger.info(f"Starting chunked fetch from external DB '{db_config.db_type}' at '{db_config.host}:{db_config.port}/{db_config.db_name}' with chunk size {chunk_size}.")

    while True:
        chunk_query = ""
        db_type_lower = db_config.db_type.lower()

        # Determine pagination syntax based on database type
        if db_type_lower in ['postgresql', 'mysql']:
            chunk_query = f"{base_query} LIMIT {chunk_size} OFFSET {offset}"
        elif db_type_lower in ['sqlserver', 'mssql']:
            # For SQL Server, OFFSET/FETCH NEXT requires an ORDER BY clause.
            # If the original query doesn't have one, add a dummy ORDER BY.
            # This ensures syntactic correctness for pagination.
            if 'ORDER BY' not in base_query.upper():
                modified_base_query = f"{base_query} ORDER BY (SELECT NULL)"
                logger.warning(f"Added 'ORDER BY (SELECT NULL)' to SQL Server query for pagination: {modified_base_query[:100]}...")
            else:
                modified_base_query = base_query
            chunk_query = f"{modified_base_query} OFFSET {offset} ROWS FETCH NEXT {chunk_size} ROWS ONLY"
        else:
            # Fallback for other DB types, might need specific implementation
            # or could use a generic approach that might not be optimal
            logger.warning(f"Using generic OFFSET/FETCH NEXT for unsupported DB type '{db_config.db_type}'. This might cause syntax errors.")
            chunk_query = f"{base_query} OFFSET {offset} ROWS FETCH NEXT {chunk_size} ROWS ONLY"

        logger.debug(f"Fetching chunk with query: {chunk_query}")
        try:
            df_chunk = read_sql(conn_str, chunk_query)
            if not isinstance(df_chunk, pl.DataFrame):
                logger.warning(f"ConnectorX returned {type(df_chunk).__name__}, converting to Polars DataFrame.")
                df_chunk = pl.DataFrame(df_chunk)

            if df_chunk.shape[0] == 0:
                logger.info("No more rows returned; ending chunk fetch.")
                break

            logger.info(f"Fetched chunk with {df_chunk.shape[0]} rows.")
            dfs.append(df_chunk)
            offset += chunk_size

        except Exception as e:
            error_message = str(e)
            if "Timed out in bb8" in error_message:
                logger.error(
                    f"Database query timed out during chunk fetch at offset {offset}: {error_message}. "
                    f"This timeout (from bb8) typically needs to be configured in the database connection string parameters "
                    f"(e.g., 'connect_timeout', 'timeout' etc. depending on DB type) or at the database server level. "
                    f"Consider adding these parameters to the 'connection_parameters' field in your ExternalDBSchema "
                    f"configuration. For example, for PostgreSQL: '?connect_timeout=10'."
                )
                raise RuntimeError(
                    f"External DB query timed out at offset {offset}. "
                    f"Possible causes: complex query, large data, network latency, or short database connection timeouts. "
                    f"Original error: {error_message}"
                )
            else:
                logger.error(f"Failed to fetch chunk at offset {offset}: {error_message}", exc_info=True)
                raise RuntimeError(f"External DB chunk fetch failed at offset {offset}: {error_message}")

    if dfs:
        full_df = pl.concat(dfs)
    else:
        full_df = pl.DataFrame()

    return full_df.lazy()

def _fetch_from_local_db(db_config: LocalDBSchema) -> pl.LazyFrame:
    """
    Fetches data from a local SQLite database.

    Args:
        db_config (LocalDBSchema): Configuration for the local SQLite database.

    Returns:
        pl.LazyFrame: A Polars LazyFrame containing the fetched data.

    Raises:
        ValueError: If 'sql_query' is empty.
        RuntimeError: If fetching from the local DB fails.
    """
    if not db_config.sql_query:
        raise ValueError("LocalDBSchema must have a non-empty 'sql_query'.")

    db_path = db_config.db_file_path
    logger.info(f"Connecting to local SQLite DB at: {db_path}")
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if db_config.initial_sql:
            logger.debug(f"Executing initial SQL: {db_config.initial_sql[:150]}...")
            cursor.executescript(db_config.initial_sql)
            conn.commit()
            logger.info("Initial SQL executed successfully.")

        logger.debug(f"Executing main SQL query: {db_config.sql_query[:150]}...")
        cursor.execute(db_config.sql_query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        df = pl.DataFrame(rows, schema=columns)
        logger.info(f"Fetched {df.shape[0]} rows from local SQLite DB.")
        return df.lazy()

    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}", exc_info=True)
        raise RuntimeError(f"Local SQLite fetch failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during local DB fetch: {e}", exc_info=True)
        raise RuntimeError(f"Local DB fetch failed: {e}")
    finally:
        if conn:
            conn.close()
            logger.debug(f"Closed SQLite connection to {db_path}")

def fetch_data(db_config: Union[ExternalDBSchema, LocalDBSchema]) -> pl.LazyFrame:
    """
    Dispatches data fetching to the appropriate database type.

    Args:
        db_config (Union[ExternalDBSchema, LocalDBSchema]): Database configuration.

    Returns:
        pl.LazyFrame: A Polars LazyFrame containing the fetched data.

    Raises:
        ValueError: If an unsupported db_config type is provided.
    """
    if isinstance(db_config, ExternalDBSchema):
        logger.info(f"Dispatching to external DB fetch (type: {db_config.db_type})")
        return _fetch_from_external_db(db_config)
    elif isinstance(db_config, LocalDBSchema):
        logger.info(f"Dispatching to local SQLite fetch (path: {db_config.db_file_path})")
        return _fetch_from_local_db(db_config)
    else:
        logger.error(f"Unsupported db_config type: {type(db_config).__name__}")
        raise ValueError(f"Unsupported db_config type: {type(db_config).__name__}. Must be ExternalDBSchema or LocalDBSchema.")
