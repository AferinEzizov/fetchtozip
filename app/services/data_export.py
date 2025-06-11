import polars as pl
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED 
from app.core.config import TEMP_DIR
import os 

def zip_export(df: pl.DataFrame, output_dir: Path, task_id: str) -> Path:
    output_dir = Path(TEMP_DIR)  # str -> Path
    zip_path = output_dir / f"{task_id}.zip"
    csv_path = output_dir / f"{task_id}.csv"
    error_path = output_dir / f"{task_id}.error"
    
    try:
        df.write_csv(csv_path)

        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zipf:
            zipf.write(csv_path, arcname="data.csv")
        
        return zip_path

    except Exception as e:
        error_path.write_text(f"An error occurred during zip export: {e}")
        raise
        
    finally:
        if csv_path.exists():
            os.remove(csv_path)


