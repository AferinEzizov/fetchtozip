
from fastapi import APIRouter, BackgroundTasks, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List, Optional, Dict
import json
import asyncio
import requests

# CONFIG FAYLLARI
from app.core.config import TEMP_DIR, URL, INPUTS, ADVANCED 
# Əsas prosessçi
from app.services.data import process 
from app.services.data_request import fetch_data
from pydantic import BaseModel

# ID UCUN
import uuid

# URL PREFIXI
router = APIRouter(prefix=URL)
TEMP_DIR = Path(TEMP_DIR)


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        self.active_connections[task_id] = websocket

    def disconnect(self, task_id: str):
        if task_id in self.active_connections:
            del self.active_connections[task_id]

    async def send_personal_message(self, message: str, task_id: str):
        if task_id in self.active_connections:
            try:
                await self.active_connections[task_id].send_text(message)
            except:
                # Connection might be closed, remove it
                self.disconnect(task_id)

manager = ConnectionManager()

# İstifadəçinin xüsusi istəkləri üçün requesti
"""
class Advanced(BaseModel):
    file_type: Optional[str] = None
    api_url: Optional[str] = None
    normalization_type: Optinal[str] = None
    rate_limit: Optional[int] = None
"""
# İstifadəçinin  Cədvəl üçün requesti
class Input(BaseModel):
    name: Optional[str] = None
    coloumn: Optional[int] = None
    change_order: Optional[int] = None 

# Prosess haqqında status
class Status(BaseModel):
    ready: str
    pending: str  
    started: str

# WebSocket endpoint for real-time notifications
@router.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await manager.connect(websocket, task_id)
    try:
        while True:
            # Keep connection alive and listen for any messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(task_id)

#Xüsusi istəklər üçün
@router.get('/advanced')  # parametrləri daxil edir
async def update_columns(file_type: Optional[str] = None, api_url: Optional[str] = None, normalization_type: Optional[str] = None):
    advanced = Advanced(
        file_type=file_type,
        api_url=api_url,
        normalization_type=normalization_type,
        rate_limit=rate_limit
    )
    
    ADVANCED.append(advanced)
    return {"message": "Advanced added successfully", "advanced": advanced}

# İstifadəçi elədiyi cədvəl dəyişikliyini INPUT listinə daxil edir
@router.get('/input')  # parametrləri daxil edir
async def update_columns(name: Optional[str] = None, coloumn: Optional[int] = None, change_order: Optional[int] = None):
    input_data = Input(
        name=name,
        coloumn=coloumn,
        change_order=change_order,
    )

    INPUTS.append(input_data)
    return {"message": "Input added successfully", "input": input_data}

async def process_with_notifications(task_id: str, inputs: List[Input]):
    try:
        await manager.send_personal_message(
            json.dumps({"status": "started", "message": "Processing started", "task_id": task_id}),
            task_id
        )
        
        if asyncio.iscoroutinefunction(process):
            result = await process(task_id, inputs)
        else:
            result = await asyncio.get_event_loop().run_in_executor(None, process, task_id, inputs)
        
        await manager.send_personal_message(
            json.dumps({"status": "completed", "message": "Processing completed", "task_id": task_id}),
            task_id
        )
        
        return result
        
    except Exception as e:
        error_path = TEMP_DIR / f"{task_id}.error"
        error_path.write_text(str(e))
        
        await manager.send_personal_message(
            json.dumps({"status": "failed", "message": str(e), "task_id": task_id}),
            task_id
        )
        raise e

# Buradan prosess başladılır
@router.post('/start')  # task_id yaradılır və queryə uyğun fayl hazırlanır
async def start(background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    
    # Add the enhanced process function to background tasks
    background_tasks.add_task(process_with_notifications, task_id, INPUTS.copy())
    
    return {"message": "Export started", "task_id": task_id}


@router.get('/table')
async def table():
    
    response = requests.get("http://localhost:3001/api/data")
    response.raise_for_status()
    return response.json()

# Status yoxlanır  
@router.get('/status/{task_id}')  # İstifadəçiyə status haqqında məlumat verilir
async def get_status(task_id: str):
    done_path = TEMP_DIR / f"{task_id}.done"
    error_path = TEMP_DIR / f"{task_id}.error"
    zip_path = TEMP_DIR / f"{task_id}.zip"
    
    if error_path.exists():
        error_message = error_path.read_text()
        return {"status": "failed", "message": error_message}
    
    if done_path.exists() or zip_path.exists():
        return {"status": "completed", "message": "Export completed successfully"}
    
    return {"status": "processing", "message": "Export is being processed"}

# Fayl yüklənir
@router.get("/download/{task_id}")  # Faylın yükləmə üçün funksiyadır
def download(task_id: str):
    zip_path = TEMP_DIR / f"{task_id}.zip"
    
    if not zip_path.exists():  # fayl olmadıqda hazırlanmadığını bildirir
        raise HTTPException(status_code=404, detail="File not ready")
    
    return FileResponse(zip_path, media_type="application/zip", filename=f"export_{task_id}.zip")

# Clear all inputs (utility endpoint)
@router.delete('/input/clear')
async def clear_inputs():
    INPUTS.clear()
    return {"message": "All inputs cleared"}

# Get current inputs (utility endpoint)  
@router.get('/input/list')
async def list_inputs():
    return {"inputs": INPUTS, "count": len(INPUTS)}
