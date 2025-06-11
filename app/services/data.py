from pathlib import Path
from app.core.config import TEMP_DIR, INPUTS, DB_URL
from app.services import data_request, data_manipulate, data_export


def process(task_id: str, inputs: list[INPUTS]):
    try:
        
        df = data_request.fetch_data(DB_URL)
        df = data_manipulate.manipulate(df, inputs)
        zip_path = data_export.zip_export(df, TEMP_DIR, task_id)
        (Path(TEMP_DIR) / f"{task_id}.done").touch()

    
    except Exception as e:
        log.error(f"[{task_id}] Failed: {e}")
        (TEMP_DIR / f"{task_id}.error").write_text(str(e))
