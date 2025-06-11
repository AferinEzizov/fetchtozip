from fastapi import  APIRouter, BackgroundTasks, HTTPException, status
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List, Optional
#CONFIG FAYLLARI
from app.core.config import TEMP_DIR, URL , INPUTS
#Əsas prosessçi
from app.services.data import process 

from pydantic import BaseModel

# iD UCUN
import uuid

#URL PREFIXI
router = APIRouter(prefix=URL)
TEMP_DIR = Path(TEMP_DIR)
# İstifadəçinin requesti
class Input(BaseModel):
    name: Optional[str] = None
    coloumn: Optional[int] = None
    change_order: Optional[int] = None 

# prosess haqqında status
class Status(BaseModel):
    ready: str
    pending: str
    started: str

# Istifadəçi elədiyi cədvəl dəyişikliyini İNPUT listinə daxil edirsiz
@router.get('/input') # parametrləri daxil edirsiz
async def update_columns(name: Optional[str],coloumn: Optional[int],change_order: Optional[int]):

    input_data = Input(
            name=name,
            coloumn=coloumn,
            change_order=change_order,
            )   
    
    INPUTS.append(input_data)

# Buradan prosess başladılır
@router.post('/start') # task_id yaradılır və queryə uyğun fayl hazırlanır
async def start(background_tasks: BackgroundTasks):
    task_id=str(uuid.uuid4())
    background_tasks.add_task(process, task_id, INPUTS)
    return {"message": "Export started", "task_id": task_id}

# Status yoxlanır
@router.post('/status{task_id}') # Istifadəçiyə status haqqında məlumat verilir
async def status(task_id):
    _done = TEMP_DIR / f"{task_id}.done" 
    _error = TEMP_DIR / f"{task_id}.error"
    _zip = TEMP_DIR / f"{task_id}.zip"
    
    #if _error:
   #     return {status: "failed","message" : _error.read_text()}
    if _done is not None:
        return {status: "Completed"}
    return {"status","processing", "message", "Export is processed"}

#Fayl yüklənir
#@router.post('/downoad/{task_id}') #
#async def downoad(task_id):
#    zip_path = TEMP_DIR / f"{task_id}.zip"

@router.get("/download/{task_id}") # Faylın yükləmə üçün funksiyadır
def download(task_id: str):


    zip_path= TEMP_DIR / f"{task_id}.zip" 


    if not zip_path.exists(): # fayl olmadıqda hazırldağını  bildirir


        raise HTTPException(status_code=404, detail="File not ready")


    return FileResponse(zip_path, media_type="application/zip",filename=f"export_{task_id}.zip") #bu xətalıdı, yükləmə baş vermir
