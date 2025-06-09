import requests
import polars as pl
from zipfile import ZipFile
from app.core.config import TEMP_DIR, INPUT
import logging

log = logging.getLogger(__name__)

def p_fetchtozip(task_id: str, num_columns: int, order: int):
    try:
        log.info(f"[{task_id}] Starting task...")
        
        response = requests.get('http://localhost:3001/api/data', timeout=10)
        response.raise_for_status()
        
        df = pl.from_records(response.json())
        log.info(f"[{task_id}] Data loaded. Shape: {df.shape}")
        
        df = df[df.columns[:num_columns]]
        
        columns = list(df.columns)
        if order == 0:
            last_col = columns.pop()
            columns.insert(0, last_col)
        
        df = df[columns]
        log.info(f"[{task_id}] Columns reordered. New order: {df.columns}")
        
        zip_path = TEMP_DIR / f"{task_id}.zip"
        with ZipFile(zip_path, "w") as zipf:
            df.write_csv(zip_path.with_suffix('.csv'))
            zipf.write(zip_path.with_suffix('.csv'), arcname="data.csv")
        log.info(f"[{task_id}] ZIP created at {zip_path}")
        
        (TEMP_DIR / f"{task_id}.done").touch()
        log.info(f"[{task_id}] Task completed successfully.")
    
    except Exception as e:
        log.error(f"[{task_id}] Failed: {e}")
        (TEMP_DIR / f"{task_id}.error").write_text(str(e))
