import uuid
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import List
from pydantic import BaseModel # BaseModel imported here, but typically from schemas file

# Assuming app.core.schemas.input_schema and Input, Configure are correctly defined for your project
from app.core.schemas.input_schema import Input, Configure # Ensure Configure is imported
from app.core.config import Inputs, Configures, TEMP_DIR # Import Configures here
# Assuming app.services.pipelines and run_pipeline are correctly defined for your project
from app.services.pipelines import run_pipeline
from pathlib import Path
import logging # Import logging for this module

# Initialize logger for this module
logger = logging.getLogger(__name__)

# IMPORTANT: Initialize an APIRouter instance for this module.
# This 'router' object will be imported by app/api/router.py
router = APIRouter()

# --- Define your specific API endpoints for 'Process' here ---

# In-memory store for task statuses and results (consider a database for persistence)
task_statuses = {}
task_results = {} # To store the path to the generated file for download

@router.post("/start", summary="Start a new processing task")
async def start_processing_task(background_tasks: BackgroundTasks):
    """
    Initiates a new background processing task using the currently stored inputs and configuration.

    Args:
        background_tasks (BackgroundTasks): FastAPI's dependency for running tasks in the background.

    Returns:
        dict: A dictionary containing a success message and the unique task ID.

    Raises:
        HTTPException: If no inputs or configuration are provided (status code 400).
    """
    # Ensure the temporary directory exists before starting any tasks
    output_dir = Path(TEMP_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    task_id = "task_" + uuid.uuid4().hex

    # Validate if inputs are provided
    if not Inputs:
        logger.warning(f"Task {task_id}: No inputs found in global Inputs list.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No inputs provided. Please add inputs using /api/export/inputs or /api/export/bulk-inputs first.")

    # Validate if a configuration is provided
    if not Configures:
        logger.warning(f"Task {task_id}: No configuration found in global Configures list.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No configuration provided. Please configure the export using /api/export/configure first.")

    # Get the active configuration. Assumes Configures contains only one item due to /configure logic.
    active_config = Configures[0]
    logger.debug(f"Task {task_id}: Active configuration found: {active_config.model_dump()}")

    # Register task as in_progress
    task_statuses[task_id] = {"status": "in_progress", "progress": 0}
    task_results[task_id] = None # Initialize result storage for this task

    # Nested function to run the pipeline and update status
    def run_and_track_pipeline():
        try:
            logger.info(f"Task {task_id}: Pipeline execution started.")
            # Pass the single active_config object to run_pipeline
            pipeline_result = run_pipeline(task_id, Inputs, active_config)
            task_statuses[task_id] = {"status": "completed"}
            task_results[task_id] = pipeline_result.get("output_path") # Store the output path for download
            logger.info(f"Task {task_id}: Pipeline completed. Output: {task_results[task_id]}")
        except Exception as e:
            error_message = f"Task {task_id}: Pipeline failed: {e}"
            logger.error(error_message, exc_info=True)
            task_statuses[task_id] = {"status": "failed", "error": str(e)}
            task_results[task_id] = None # Clear result path on failure

    background_tasks.add_task(run_and_track_pipeline)

    logger.info(f"Processing task {task_id} initiated with {len(Inputs)} inputs.")
    return {"message": "Task started", "task_id": task_id}


@router.get("/status/{task_id}", summary="Get the status of a processing task")
async def get_processing_status(task_id: str):
    """
    Retrieves the current status of a given processing task.

    Args:
        task_id (str): The unique identifier of the task.

    Returns:
        dict: A dictionary containing the task ID and its status, progress, or error message.

    Raises:
        HTTPException: If the task ID is not found (status code 404).
    """
    if task_id not in task_statuses:
        logger.warning(f"Status request for unknown task_id: {task_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    logger.debug(f"Status for task {task_id}: {task_statuses[task_id]}")
    return {"task_id": task_id, **task_statuses[task_id]}


@router.get("/download/{task_id}", summary="Download the output of a completed task")
async def download_task_output(task_id: str):
    """
    Allows downloading the output file of a successfully completed processing task.

    Args:
        task_id (str): The unique identifier of the completed task.

    Returns:
        FileResponse: The output file for download.

    Raises:
        HTTPException:
            - If the task is not found (404).
            - If the task is not yet completed (409 Conflict).
            - If the task failed (500 Internal Server Error).
            - If the output file is not found (404, even if task completed).
    """
    from fastapi.responses import FileResponse # Import here to avoid circular dependencies if used elsewhere

    if task_id not in task_statuses:
        logger.warning(f"Download request for unknown task_id: {task_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    task_status_info = task_statuses[task_id]
    current_status = task_status_info.get("status")
    output_file_path = task_results.get(task_id)

    if current_status != "completed":
        if current_status == "failed":
            logger.error(f"Download request for failed task {task_id}.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Task failed: {task_status_info.get('error', 'Unknown error')}")
        else:
            logger.info(f"Download request for in-progress task {task_id}. Current status: {current_status}")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Task {task_id} is not yet completed. Current status: {current_status}")

    if not output_file_path:
        logger.error(f"Download request for completed task {task_id}, but output_path is missing.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Output file path not found for completed task.")

    file_path = Path(output_file_path)
    if not file_path.exists():
        logger.error(f"Download request for task {task_id}: File not found at {file_path}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Output file not found on server.")

    # Determine media type based on file extension
    media_type = "application/octet-stream" # Default
    if file_path.suffix == ".csv":
        media_type = "text/csv"
    elif file_path.suffix == ".json":
        media_type = "application/json"
    elif file_path.suffix == ".xlsx":
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif file_path.suffix == ".zip":
        media_type = "application/zip"

    logger.info(f"Serving file {file_path} for task {task_id}")
    return FileResponse(path=file_path, filename=file_path.name, media_type=media_type)


@router.delete("/cancel/{task_id}", summary="Cancel a processing task")
async def cancel_processing_task(task_id: str):
    """
    Attempts to cancel a running processing task.
    Note: True cancellation requires a more robust async task management system (e.g., Celery, RQ).
    This implementation marks the task for cancellation.

    Args:
        task_id (str): The unique identifier of the task to cancel.

    Returns:
        dict: A message indicating the cancellation status.

    Raises:
        HTTPException: If the task is not found or cannot be canceled (status code 404 or 400).
    """
    if task_id in task_statuses:
        current_status = task_statuses[task_id]["status"]
        if current_status == "in_progress":
            task_statuses[task_id]["status"] = "cancel_requested"
            logger.info(f"Task {task_id} cancellation requested.")
            return {"message": f"Task {task_id} cancellation requested.", "status": "cancel_requested"}
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Task {task_id} cannot be canceled as it is in '{current_status}' state.")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
