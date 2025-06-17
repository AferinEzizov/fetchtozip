import logging
from typing import List, Optional, Any, Union
from pathlib import Path

# Assuming these modules and schemas are correctly defined elsewhere in your project
# IMPORTANT: Configures is a global variable from app.core.config, managed by API.
# It should NOT be redefined or hardcoded in this file.
from app.core.config import DB_URL, TEMP_DIR
from app.core.schemas.input_schema import Input, Configure
from app.services.requests.http_client import fetch_data
from app.services.process.process import process # Assuming this exists and returns processed data
from app.services.export._zip import zip_export
#from app.services.export._json import json_export
#from app.services.export._csv import csv_export
#from app.services.export._xlsx import xlsx_export

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Define the expected return type for the process function
# Assuming 'process' returns a data structure suitable for export (e.g., a Polars DataFrame)
ProcessedDataType = Any

def run_pipeline(task_id: str, inputs: List[Input], configuration: Configure) -> dict:
    """
    Orchestrates the entire data processing pipeline:
    1. Fetches data from a specified URL.
    2. Processes the fetched data based on provided inputs (e.g., renames columns).
    3. Exports the processed data to the specified format (CSV, JSON, XLSX, or ZIP).

    Args:
        task_id (str): A unique identifier for the processing task.
        inputs (List[Input]): A list of input configurations for data processing.
        configuration (Configure): The configuration for defining the output file type
                                   and other export settings (rate limits, page limits, etc.).

    Returns:
        dict: A dictionary containing the task ID and the path to the generated output file.

    Raises:
        Exception: Re-raises any exception encountered during the pipeline execution
                   after logging the error details.
    """
    try:
        # Validate inputs
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("task_id must be a non-empty string")

        if not isinstance(inputs, list):
            raise ValueError("inputs must be a list")

        if configuration is None:
            raise ValueError("configuration cannot be None")

        logger.info(f"Pipeline: Starting for task_id={task_id}")

        # Ensure the temporary directory exists
        output_dir = Path(TEMP_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Pipeline: Output directory ensured at {output_dir}")

        # Validate DB_URL
        if not DB_URL or not isinstance(DB_URL, str):
            raise ValueError("DB_URL must be a valid non-empty string")

        # 1. Fetch data from the URL
        logger.debug(f"Pipeline: Fetching data from URL: {DB_URL} with rate_limit={getattr(configuration, 'rate_limit', None)}, page_limit={getattr(configuration, 'page_limit', None)}")

        # Safely get optional parameters with defaults
        rate_limit = getattr(configuration, 'rate_limit', None)
        page_limit = getattr(configuration, 'page_limit', None)

        # Pass optional rate_limit and page_limit if they exist in the configuration
        lazy_frame = fetch_data(
            DB_URL,
            rate_limit=rate_limit,
            page_limit=page_limit
        )

        # Validate fetched data
        if lazy_frame is None:
            raise ValueError("Failed to fetch data: received None")

        logger.debug(f"Pipeline: Fetched raw data successfully. Data type: {type(lazy_frame)}")

        # Ensure we have a Polars LazyFrame
        try:
            import polars as pl
            if not isinstance(lazy_frame, pl.LazyFrame):
                raise ValueError(f"Expected pl.LazyFrame, got {type(lazy_frame)}")

            # Pass the LazyFrame directly to processing
            data = lazy_frame
            logger.debug("Pipeline: LazyFrame ready for processing")

        except ImportError:
            raise ImportError("polars library is required for data processing")

        # 2. Process data
        # Debug: Check what we're actually passing to process()
        logger.debug(f"Pipeline: About to process data. Data type: {type(data)}")
        logger.debug(f"Pipeline: Data repr: {repr(data)}")

        # Additional check before processing
        try:
            import polars as pl
            if isinstance(data, pl.LazyFrame):
                logger.debug(f"Pipeline: Confirmed LazyFrame with schema: {data.schema}")
            else:
                logger.error(f"Pipeline: ERROR - Expected LazyFrame, got {type(data)}")
                logger.error(f"Pipeline: Data content: {str(data)[:200]}...")
                raise ValueError(f"Expected LazyFrame, got {type(data)}: {str(data)[:100]}...")
        except Exception as debug_error:
            logger.error(f"Pipeline: Debug check failed: {debug_error}")
            raise

        logger.debug(f"Pipeline: Processing data for task_id={task_id} with {len(inputs)} inputs.")
        processed_output_path = process(data, task_id, inputs)  # This returns a Path to CSV file

        # Validate processed data
        if processed_output_path is None:
            raise ValueError("Data processing failed: received None")

        if not isinstance(processed_output_path, Path):
            raise ValueError(f"Expected Path from process(), got {type(processed_output_path)}")

        logger.debug(f"Pipeline: Data processed successfully, output at: {processed_output_path}")

        # 3. Handle different export formats
        file_type = getattr(configuration, 'file_type', 'csv')
        if file_type:
            file_type = str(file_type).lower().strip()
        else:
            file_type = "csv"  # Default fallback

        logger.debug(f"Pipeline: Requested file_type: {file_type}")

        final_output_path: Optional[Path] = None

        if file_type == "csv":
            # Process function already created CSV
            final_output_path = processed_output_path
            logger.debug(f"Pipeline: Using existing CSV: {final_output_path}")
        elif file_type == "json":
            # Convert CSV to JSON
            df = pl.read_csv(processed_output_path)
            json_path = processed_output_path.with_suffix('.json')
            df.write_json(json_path)
            final_output_path = json_path
            logger.debug(f"Pipeline: Converted to JSON: {final_output_path}")
        elif file_type == "xlsx":
            # Convert CSV to XLSX
            df = pl.read_csv(processed_output_path)
            xlsx_path = processed_output_path.with_suffix('.xlsx')
            df.write_excel(xlsx_path)
            final_output_path = xlsx_path
            logger.debug(f"Pipeline: Converted to XLSX: {final_output_path}")
        elif file_type == "zip":
            # Zip the existing CSV
            final_output_path = zip_export(processed_output_path, task_id)
            logger.debug(f"Pipeline: Zipped CSV: {final_output_path}")
        else:
            raise ValueError(f"Unsupported file type for export: '{file_type}'. Supported types: csv, json, xlsx, zip")

        # Validate final output
        if final_output_path is None:
            raise ValueError("Export operation failed: no output file generated")

        if not isinstance(final_output_path, (str, Path)):
            raise ValueError(f"Invalid output path type: {type(final_output_path)}")

        # Convert to Path object if it's a string
        if isinstance(final_output_path, str):
            final_output_path = Path(final_output_path)

        # Verify the file actually exists
        if not final_output_path.exists():
            raise FileNotFoundError(f"Generated output file does not exist: {final_output_path}")

        logger.info(f"Pipeline: Task {task_id} completed successfully. Final output at: {final_output_path}")

        # Return the path to the generated file as string for JSON serialization
        return {
            "task_id": str(task_id),
            "output_path": str(final_output_path.resolve()),  # Use resolve() for absolute path
            "file_type": file_type,
            "file_size": final_output_path.stat().st_size if final_output_path.exists() else 0
        }

    except Exception as e:
        error_msg = f"Pipeline failed for task_id={task_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        # Re-raise the exception so it can be caught upstream (e.g., by FastAPI)
        raise RuntimeError(error_msg) from e
