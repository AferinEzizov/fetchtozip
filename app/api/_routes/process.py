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

task_statuses = {}

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

    # Validate if inputs Advancedare provided
    if not Inputs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No inputs provided.")

    # Register task as in_progress
    task_statuses[task_id] = {"status": "in_progress", "progress": 0}

    def run_and_track():
           try:
               run_pipeline(task_id, Inputs, Configures)
               task_statuses[task_id] = {"status": "completed"}
           except Exception as e:
               task_statuses[task_id] = {"status": "failed", "error": str(e)}

    background_tasks.add_task(run_and_track)

    print(f"Processing task {task_id} initiated with {len(Inputs)} inputs.")
    return {"message": "Task started", "task_id": task_id}


@router.get("/status/{task_id}", summary="Get the status of a processing task")
async def get_processing_status(task_id: str):
    ""
    if task_id not in task_statuses:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return {"task_id": task_id, **task_statuses[task_id]}


@router.delete("/cancel/{task_id}", summary="Cancel a processing task")
async def cancel_processing_task(task_id: str):
    # You'd need real async task manager (Celery, RQ, etc) to cancel
    if task_id in task_statuses and task_statuses[task_id]["status"] == "in_progress":
        task_statuses[task_id]["status"] = "cancel_requested"
        return {"message": f"Task {task_id} cancellation requested.", "status": "cancel_requested"}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found or already completed")
