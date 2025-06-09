import requests
import polars as pl
from pathlib import Path
from zipfile import ZipFile 
import logging


TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

SOURCE_URL = "http://127.0.0.1:8080/data.xlsx"

log = logging.getLogger(__name__)

def p_fetchtozip(task_id: str):
    try:
        
        log.info(f"[{task_id}] Starting task...")

        excel_path = TEMP_DIR / f"{task_id}.xlsx"
        response = requests.get(SOURCE_URL, timeout=10)
        response.raise_for_status()
        excel_path.write_bytes(response.content)
        
        log.info(f"[{task_id}] Excel downloaded.")

        df = pl.read_excel(excel_path)
        log.info(f"[{task_id}] Excel loaded. Shape: {df.shape}")


        required_cols = {"Gender", "Age"}
        if not required_cols.issubset(set(df.columns)):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing columns: {missing}")


        df = df.rename({
                    "Gender": "Cinsiyyet",
                    "Age":"Yas"
                })

        df = df.select(["Cinsiyyet","Yas"])
        log.info(f"[{task_id}] Columns renamed and reordered.")

        processed_path = TEMP_DIR / f"{task_id}_p.xlsx"
        df.write_excel(processed_path)
        
        log.info(f"[{task_id}] Processed Excel saved.")

        zip_path = TEMP_DIR / f"{task_id}.zip"

        with ZipFile(zip_path, "w") as zipf:
            zipf.write(processed_path, arcname="data.xlsx")
        log.info(f"[{task_id}] ZIP created at {zip_path}")
        
        (TEMP_DIR / f"{task_id}.done").touch()

        log.info(f"[{task_id}] Task completed successfully.")
    
    except Exception as e:
        log.error(f"[{task_id}] Failed: {e}")
        (TEMP_DIR / f"{task_id}.error".write_text(str(e)))
