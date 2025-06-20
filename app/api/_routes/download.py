import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pathlib import Path

from app.core.config import TEMP_DIR # Ensures TEMP_DIR is a Path object

# Import WebSocket notification functions
from app.api._routes.websocket import (
    notify_download_processing,
    notify_download_start,
    notify_download_end
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get(
    "/downloads/download/{task_id}", # Updated path to '/downloads/download'
    summary="Download a processed file by task ID",
    response_class=FileResponse,
    responses={
        200: {"description": "File successfully downloaded", "content": {"application/zip": {}}},
        404: {"description": "File not found"}
    }
)
async def download_file(task_id: str):
    """
    Allows clients to download a processed file (expected to be a ZIP archive)
    identified by its unique task ID. The file is located within a task-specific
    subdirectory of the global temporary directory.

    Sends real-time WebSocket notifications at different stages of the download:
    - `notify_download_processing`: When the server starts preparing the download.
    - `notify_download_start`: Just before the file transfer begins.
    - `notify_download_end`: When the file transfer is complete (or connection closes).

    Args:
        task_id (str): The unique identifier for the processing task that generated the file.

    Returns:
        FileResponse: The ZIP file to be downloaded.

    Raises:
        HTTPException (404 Not Found): If the specified ZIP file does not exist.
    """
    # Construct the expected path to the ZIP file within the task-specific temporary directory
    # Assumes run_pipeline saves final output (e.g., zip) to TEMP_DIR / task_id / {task_id}.zip
    task_specific_dir = TEMP_DIR / task_id
    zip_path = task_specific_dir / f"{task_id}.zip"

    logger.info(f"Attempting to serve download for task_id='{task_id}' from path: '{zip_path.resolve()}'")

    if not zip_path.exists():
        logger.warning(f"Download failed: Zip file not found for task_id='{task_id}' at '{zip_path.resolve()}'.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found for task ID: {task_id}. Please ensure processing is complete or check the task ID."
        )

    # Notify WebSocket clients that download processing has started
    await notify_download_processing(task_id)

    response = FileResponse(
        path=str(zip_path), # FileResponse expects a string path
        filename=f"{task_id}.zip", # Name client will see for the downloaded file
        media_type="application/zip", # Standard MIME type for zip files
    )

    # Notify WebSocket clients that the download has started (actual file transfer begins now)
    await notify_download_start(task_id)

    @response.call_on_close
    async def on_download_complete():
        """
        This callback is executed when the FileResponse stream is closed,
        indicating the download is complete or was interrupted.
        It cleans up the task-specific temporary directory.
        """
        logger.info(f"Download stream closed for task_id='{task_id}'. Notifying clients.")
        await notify_download_end(task_id)
        
        # Clean up the entire task-specific directory after the file has been served
        # This is important to free up disk space for temporary files.
        try:
            if task_specific_dir.exists():
                shutil.rmtree(task_specific_dir)
                logger.info(f"Cleaned up task-specific temporary directory: '{task_specific_dir.resolve()}'")
            else:
                logger.debug(f"Task-specific directory '{task_specific_dir.resolve()}' not found during cleanup, perhaps already removed.")
        except OSError as e:
            logger.error(f"Failed to delete task-specific directory '{task_specific_dir.resolve()}': {e}", exc_info=True)

    return response

# Added `shutil` import at the top
import shutil
