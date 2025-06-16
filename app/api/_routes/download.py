from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from app.core.config import TEMP_DIR

router = APIRouter()

@router.get("/download/{task_id}", tags=["Download"])
async def download_file(task_id: str):
    zip_path = Path(TEMP_DIR) / f"{task_id}.zip"

    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Zip File not found.")

    return FileResponse(
        path=str(zip_path),
        filename = f"{task_id}.zip",
        media_type="application/zip"
    )
