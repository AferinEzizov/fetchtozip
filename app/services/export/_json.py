import polars as pl
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from app.core.config import TEMP_DIR
import os

def zip_export_json(task_id: str) -> Path:
    output_dir = Path(TEMP_DIR)
    csv_path = output_dir / f"{task_id}.csv"
    json_path = output_dir / f"{task_id}.json"
    zip_path = output_dir / f"{task_id}.zip"
    error_path = output_dir / f"{task_id}.error"

    try:
        df = pl.read_csv(csv_path)
        df.write_json(json_path, orient="records")

        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zipf:
            zipf.write(json_path, arcname="data.json")

        return zip_path

    except Exception as e:
        error_path.write_text(f"Error during JSON zip export: {e}")
        raise

    finally:
        if csv_path.exists():
            os.remove(csv_path)
        if json_path.exists():
            os.remove(json_path)
