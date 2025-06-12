import uuid
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import List
from pydantic import BaseModel
# Assuming app.core.schemas.input_schema and Input are correctly defined for your project
from app.core.schemas.input_schema import Input
from app.core.config import Inputs, TEMP_DIR
# Assuming app.services.pipelines and run_pipeline are correctly defined for your project
from app.services.pipelines import run_pipeline
from pathlib import Path


# IMPORTANT: Initialize an APIRouter instance for this module.
# This 'router' object will be imported by app/api/router.py
router = APIRouter()

# --- Define your specific API endpoints for 'Process' here ---


@router.post("/start", summary="Start a new processing task")
async def start_processing_task(background_tasks: BackgroundTasks):
    """
    Initiates a new background processing task with provided inputs from the request body.

    Args:
        request_data (StartProcessRequest): The request body containing the URL and a list of input data items.
        background_tasks (BackgroundTasks): FastAPI's dependency for running tasks in the background.

    Returns:
        dict: A dictionary containing a success message and the unique task ID.

    Raises:
        HTTPException: If no inputs are provided (status code 400).
    """
    output_dir = Path(TEMP_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    task_id = "task_" + uuid.uuid4().hex

    # Validate if inputs are provided
    if not Inputs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No inputs provided.")

    # Add the run_pipeline function to background tasks.
    # The 'url' and 'inputs' received from the request body are passed directly.
    background_tasks.add_task(run_pipeline, task_id, Inputs)

    print(f"Processing task {task_id} initiated with {len(Inputs)} inputs.")
    return {"message": "Task started", "task_id": task_id}

@router.get("/status/{task_id}", summary="Get the status of a processing task")
async def get_processing_status(task_id: str):
    """
    Retrieves the current status of a previously started processing task.
    """
    # In a real application, you would query a database or
    # task queue to get the actual status for the given task_id.
    # For demonstration, let's mock some statuses.
    if task_id == "some_unique_task_id_123":
        return {"task_id": task_id, "status": "in_progress", "progress": 50}
    elif task_id == "completed_task_xyz":
        return {"task_id": task_id, "status": "completed", "result": "output_data_here"}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

@router.delete("/cancel/{task_id}", summary="Cancel a processing task")
async def cancel_processing_task(task_id: str):
    """
    Attempts to cancel a running processing task.
    """
    # Implement actual cancellation logic here (e.g., stopping a celery task)
    print(f"Attempting to cancel task {task_id}.")
    if task_id == "some_unique_task_id_123":
        return {"message": f"Task {task_id} cancellation requested.", "status": "pending_cancellation"}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found or already completed")

# Add more process-related endpoints as needed (e.g., /upload, /download, /configure)
