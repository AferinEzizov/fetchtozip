from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from app.services.fetchtozip import p_fetchtozip
from pathlib import Path 

import uuid 

router = APIRouter()
TEMP_DIR = Path("temp") # Fayl əmliyyatlarının yerinə yetirilir. config.py-a köçürüləcək

# Burada istənilən datanın ziplənməsi üçün request atılır
@router.post("/start-export", status_code=202)
async def start_export(background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4()) # Hər task üçün unique ID verilir 
    background_tasks.add_task(p_fetchtozip, task_id) # FetchtoZip çağrılır və arxplanda işləyir
    return {"message":"Export started", "task_id": task_id} 


@router.get("/status/{task_id}") # İstifadçiyə prosessin başlandığını / davam etdiyini / qurtardığını bildirir
def status(task_id:str): 
    done_file = TEMP_DIR / f"{task_id}.done" 
    error_file = TEMP_DIR / f"{task_id}.error"
    zip_file = TEMP_DIR / f"{task_id}.zip"

    if error_file.exists(): # Error faylının yaradalığında. erroru return eliyir
        return {"status": "failed","message": error_file.read_text()}
    if done_file.exists() and zip_file.exists(): # Yaradılığını göstərir
        return {"status": "completed"}
    return {"status": "processing"} davam etdiyini göstərir

@router.get("/download/{task_id}") # Faylın yükləmə üçün funksiyadır
sef download(task_id: str):
    zip_path= TEMP_DIR / f"{task_id}.zip" 
    if not zip_path.exists(): # fayl olmadıqda hazırldağını  bildirir
        raise HTTPException(status_code=404, detail="File not ready")
    return FileResponse(zip_path, media_type="application/zip",filename=f"export_{task_id}.zip") #bu xətalıdı, yükləmə baş vermir
