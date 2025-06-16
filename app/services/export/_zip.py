import polars as pl
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from app.core.config import TEMP_DIR
import os
import logging

logger = logging.getLogger(__name__)

def zip_export(csv_path: Path, task_id: str) -> Path:
    output_dir = Path(TEMP_DIR)
    zip_path = output_dir / f"{task_id}.zip"
    error_path = output_dir / f"{task_id}.error"

    try:
        logger.debug(f"zip_export: Reading CSV from {csv_path}")
        df = pl.read_csv(csv_path)  # Will raise if file doesn't exist or unreadable

        logger.debug(f"zip_export: Creating ZIP at {zip_path}")
        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zipf:
            zipf.write(csv_path, arcname="data.csv")

        logger.info(f"zip_export: Successfully zipped to {zip_path}")
        return zip_path

    except Exception as e:
        logger.error(f"zip_export: Failed to export CSV to zip for {task_id}: {e}")
        error_path.write_text(f"An error occurred during zip export: {e}")
        raise

    finally:
        if csv_path.exists():
            logger.debug(f"zip_export: Cleaning up temporary CSV at {csv_path}")
            os.remove(csv_path)
