from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResonse
from app.services.fetchtozip import p_fetchtozip
from pathlib import Path 

import uuid 

router = APIRouter()
TEMP_DIR = Path("temp")

@router.post("/start-export", status_code=202)
async def start_export(background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    background_tasks.add_task(p_fetchtozip, task_id)
    return {"message":"Export started", "task_id": task_id}


@router.get("/status/{task_id}")
def status(task_id:str):
    done_file = TEMP_DIR / f"{task_id}.done"
    error_file = TEMP_DIR / f"{task_id}.error"
    zip_file = TEMP_DIR / f"{task_id}.zip"

    if error_file.exists():
        return {"status": "failed","message": error_file.read_text()}
    if done_file.exists() and zip_file.exists():
        return {"status": "completed"}
    return {"status": "processing"}

@router.get("/download/{task_id}")
def download(task_id: str):
    zip_path= TEMP_DIR / f"{task_id}.zip"
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="File not ready")
    return FileResonse(zip_path, media_type="application/zip"),filename=f"export_task_id}.zip")
