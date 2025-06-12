import polars as pl
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from app.core.config import TEMP_DIR
import os

def zip_export(task_id: str) -> Path:
    output_dir = Path(TEMP_DIR)
    csv_path = output_dir / f"{task_id}.csv"
    zip_path = output_dir / f"{task_id}.zip"
    error_path = output_dir / f"{task_id}.error"

    try:
        # Load CSV to ensure it exists and is readable (optional)
        df = pl.read_csv(csv_path)

        # Write zip file with CSV inside as 'data.csv'
        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zipf:
            zipf.write(csv_path, arcname="data.csv")

        return zip_path

    except Exception as e:
        error_path.write_text(f"An error occurred during zip export: {e}")
        raise

    finally:
        if csv_path.exists():
            os.remove(csv_path)
