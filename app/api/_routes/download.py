from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from app.core.config import TEMP_DIR

from app.api._routes.websocket import (
    notify_download_processing,
    notify_download_start,
    notify_download_end
)

router = APIRouter()


@router.get("/download/{task_id}", tags=["Download"])
async def download_file(task_id: str):
    """
    Download a processed ZIP file by task ID.

    Sends real-time WebSocket notifications for:
    - Processing start
    - Download start
    - Download complete
    """
    zip_path = Path(TEMP_DIR) / f"{task_id}.zip"

    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Zip File not found.")

    await notify_download_processing(task_id)

    response = FileResponse(
        path=str(zip_path),
        filename=f"{task_id}.zip",
        media_type="application/zip"
    )

    await notify_download_start(task_id)

    @response.call_on_close
    async def done():
        await notify_download_end(task_id)

    return response

