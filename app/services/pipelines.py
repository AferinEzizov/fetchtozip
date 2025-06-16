# app/services/pipelines.py

import logging
from typing import List
# from pathlib import Path

# Assuming these modules and schemas are correctly defined elsewhere in your project
from app.core.config import DB_URL
from app.core.schemas.input_schema import Input, Configure
from app.services.requests.http_client import fetch_data
from app.services.process.process import process
from app.services.export._zip import zip_export
from app.services.export._json import json_export
from app.services.export._csv import csv_export
from app.services.export._xlsx import xlsx_export

# Initialize logger for this module
logger = logging.getLogger(__name__)

def run_pipeline(task_id: str, inputs: List[Input], configuration: List[Configure]) -> dict:
    """
    Orchestrates the entire data processing pipeline:
    1. Fetches data from a specified URL.
    2. Processes the fetched data based on provided inputs (e.g., renames columns).
    3. Zips the resulting CSV output.

    Args:
        task_id (str): A unique identifier for the processing task.
        url (str): The URL from which to fetch the initial data.
        inputs (List[Input]): A list of input configurations for data processing.
        configure (List[Configure]): A list of config confguration for configure the file that exports.
        Returns:
        dict: A dictionary containing the task ID and the path to the generated zip file.

    Raises:
        Exception: Re-raises any exception encountered during the pipeline execution
                   after logging the error details.
    """
    try:
        logger.info(f"Pipeline: Starting for task_id={task_id}")

        # 1. Fetch data from the URL
        logger.debug(f"Pipeline: Fetching data from URL: {DB_URL}")
        data = fetch_data(DB_URL, rate_limit = configuration.rate_limit, page_limit = configuration.page_limit)
        logger.debug(f"Pipeline: Fetched data with columns: {data.schema}")
        # 2. Process data and save as CSV
        # The 'process' function is expected to return the Path object of the CSV file.
        logger.debug(f"Pipeline: Processing data for task_id={task_id} with {len(inputs)} inputs.")

        # Export based on file_type
        file_type = configuration.file_type.lower() if configuration.file_type else "csv"
        output_path: Path

        if file_type == "csv":
            output_path = csv_export(processed_csv_path, task_id)
        elif file_type == "zip":
            output_path = zip_export(processed_csv_path, task_id)
        elif file_type == "json":
            output_path = json_export(processed_csv_path, task_id)
        elif file_type == "xlsx":
            output_path = xlsx_export(processed_csv_path, task_id)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    except Exception as e:
        # Log the full traceback for better debugging
        logger.error(f"Pipeline: Failed for task_id={task_id}: {e}", exc_info=True)
        raise # Re-raise the exception so it can be caught upstream (e.g., by FastAPI)
