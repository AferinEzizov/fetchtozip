import logging
import uuid # For generating unique task IDs if not provided
from typing import List, Dict, Any, Union, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Import Pydantic schemas for request body validation
from app.core.schemas.input_schema import Input, Configure

# Import the core pipeline orchestration function from its actual location
# Assuming 'run_pipeline' function is in 'app/services/pipeline/run_pipeline.py'
from app.services.pipelines import run_pipeline

logger = logging.getLogger(__name__)

router = APIRouter()

# Define a Pydantic model for the pipeline trigger request body
class PipelineTriggerRequest(BaseModel):
    """
    Schema for the request body to trigger the data processing pipeline.
    """
    task_id: Optional[str] = Field(None, description="Optional unique ID for the task. If not provided, a UUID will be generated.")
    inputs: List[Input] = Field([], description="List of input configurations for column transformations.")
    configuration: Configure = Field(..., description="The application configuration for this pipeline run, including DB config and file type.")


@router.post("/run", summary="Trigger the data processing and export pipeline", response_model=Dict[str, Union[str, int]])
async def trigger_pipeline(request_body: PipelineTriggerRequest) -> Dict[str, Union[str, int]]:
    """
    Initiates the full data processing and export pipeline.
    
    This endpoint takes a task_id (optional), a list of input transformations,
    and a complete application configuration (including database details)
    to fetch, process, and export data.

    Args:
        request_body (PipelineTriggerRequest): The request body containing:
            - task_id (Optional[str]): A unique identifier for this task. If not provided, a UUID will be generated.
            - inputs (List[Input]): List of column transformation rules.
            - configuration (Configure): The full configuration for this pipeline run.

    Returns:
        Dict[str, Union[str, int]]: A dictionary with task status and output path on success.

    Raises:
        HTTPException: For various errors encountered during pipeline execution,
                       translated from the underlying service's exceptions.
    """
    # Generate a task_id if not provided by the client
    current_task_id = request_body.task_id if request_body.task_id else str(uuid.uuid4())
    logger.info(f"API: Received pipeline trigger request for task_id='{current_task_id}'")

    try:
        # Call the core run_pipeline service function
        # This function resides in app/services/pipeline/run_pipeline.py
        result = await run_pipeline(
            task_id=current_task_id,
            inputs=request_body.inputs,
            configuration=request_body.configuration # Pass the Configure object directly
        )
        logger.info(f"API: Pipeline for task_id='{current_task_id}' completed successfully.")
        return {
            "message": "Pipeline initiated successfully.",
            "task_id": result["task_id"],
            "output_path": result["output_path"],
            "file_type": result["file_type"],
            "file_size": result["file_size"]
        }
    except HTTPException as http_exc:
        # Re-raise HTTPExceptions directly, as they are already formatted (e.g., from validation errors)
        logger.error(f"API: Pipeline for task_id='{current_task_id}' failed with HTTP error: {http_exc.detail}", exc_info=True)
        raise http_exc
    except ValueError as e:
        logger.error(f"API: Pipeline for task_id='{current_task_id}' failed due to input validation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pipeline input validation error: {e}"
        )
    except FileNotFoundError as e:
        logger.error(f"API: Pipeline for task_id='{current_task_id}' failed due to file not found: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline file not found error: {e}"
        )
    except RuntimeError as e:
        # Catch generic RuntimeErrors from the run_pipeline service
        logger.error(f"API: Pipeline for task_id='{current_task_id}' failed unexpectedly: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution failed: {e}"
        )
    except Exception as e:
        # Catch any other unhandled exceptions
        logger.error(f"API: An unhandled error occurred during pipeline execution for task_id='{current_task_id}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during pipeline execution: {e}"
        )
