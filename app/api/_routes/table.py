import logging
from typing import Dict, Any, Union, List # Added List for table data structure
from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from app.core.schemas.input_schema import ExternalDBSchema, LocalDBSchema
from app.services.requests.fetch import fetch_data # Re-use the fetch_data service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/table/data", summary="Fetch database content as JSON", response_model=Dict[str, Any])
async def fetch_table_data(
    db_config: Union[ExternalDBSchema, LocalDBSchema] # Accept either DB config type directly in the request body
) -> Dict[str, Any]:
    """
    Fetches data from a specified database (external or local SQLite) using the provided
    configuration and returns the data as a list of dictionaries (JSON).

    This endpoint is for direct data retrieval and does not involve the full processing pipeline
    (i.e., no column renaming, reordering, or special file exports beyond JSON).

    Args:
        db_config (Union[ExternalDBSchema, LocalDBSchema]): The database configuration
                                                          including connection details and SQL query.
                                                          Provided directly in the request body.

    Returns:
        Dict[str, Any]: A dictionary containing the fetched 'data' as a list of dictionaries
                        and a 'message'.

    Raises:
        HTTPException (400 Bad Request): If there's an issue with the DB config or fetching input.
        HTTPException (500 Internal Server Error): For unexpected errors during data retrieval from the database.
    """
    logger.info("Received request to fetch raw table data as JSON.")
    try:
        # Use the common fetch_data service function to get a Polars LazyFrame
        lazy_frame = fetch_data(db_config)
        
        # Collect the LazyFrame into an in-memory DataFrame
        df = lazy_frame.collect()
        
        if df.is_empty():
            logger.warning("Fetched data is empty for the given DB config and query.")
            return {"message": "Successfully fetched data, but the result is empty.", "data": []}

        # Convert Polars DataFrame to a list of Python dictionaries, which FastAPI will then
        # automatically serialize to a JSON array of objects.
        data_as_list_of_dicts: List[Dict[str, Any]] = df.to_dicts()

        logger.info(f"Successfully fetched {len(data_as_list_of_dicts)} rows from database for JSON output.")
        return {
            "message": "Data fetched successfully",
            "data": data_as_list_of_dicts
        }
    except ValidationError as e:
        logger.error(f"Invalid DB configuration provided in request body: {e.errors()}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid database configuration provided: {e.errors()}"
        )
    except ValueError as e: # Catch ValueErrors specifically from fetch_data (e.g., missing sql_query)
        logger.error(f"Data fetching input error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Data fetching input error: {e}"
        )
    except RuntimeError as e: # Catch RuntimeErrors specifically from fetch_data service failures
        logger.error(f"Database fetching service failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database fetching service failed: {e}"
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching table data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )
