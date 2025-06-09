from fastapi import APIRouter, BackgroundTasks, HTTPException, status 
from fastapi.responses import FileResponse
from app.services.fetchtozip import p_fetchtozip
from app.core.config import TEMP_DIR, INPUT
import uuid

router = APIRouter(prefix="/api/export", tags=["Export Operations"]) 


@router.get('/inputname/{name}', summary="Update column name for the second column")
async def inputnamey(name: str):
    """Update column name for the second column"""
    INPUT[2] = name
    return {"message": f"Column name updated to: {name}"}

@router.get('/inputorder/{order}', summary="Update column order for the third column")
async def inputorder(order: int):
    """Update column order for the third column"""
    if not 0 <= order:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order must be 0 or 1") 
    INPUT[3] = order
    return {"message": f"Column order updated to: {order}"}

@router.post("/start", status_code=status.HTTP_202_ACCEPTED, summary="Initiate a new data export process") 
async def start_export(background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    background_tasks.add_task(p_fetchtozip, task_id, INPUT[3], INPUT[2])
    return {"message": "Export started", "task_id": task_id}

@router.get("/status/{task_id}", summary="Get the current status of an export task")
def status(task_id: str):
    done_file = TEMP_DIR / f"{task_id}.done"
    error_file = TEMP_DIR / f"{task_id}.error"
    zip_file = TEMP_DIR / f"{task_id}.zip"

    if error_file.exists():
        return {"status": "failed", "message": error_file.read_text()}
    if done_file.exists() and zip_file.exists():
        return {"status": "completed"}
    return {"status": "processing", "message": "Export is currently being processed."}

@router.get("/download/{task_id}", summary="Download the completed export file")
def download(task_id: str):
    zip_path = TEMP_DIR / f"{task_id}.zip"
    if not zip_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not ready") # Used status.HTTP_404_NOT_FOUND
    return FileResponse(zip_path, media_type="application/zip", filename=f"{task_id}.zip")
