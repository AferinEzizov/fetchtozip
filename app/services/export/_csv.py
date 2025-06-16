import polars as pl
from pathlib import Path
from app.core.config import TEMP_DIR
import os
import logging

logger = logging.getLogger(__name__)

def csv_export(csv_path: Path, task_id: str) -> Path:
    output_dir = Path(TEMP_DIR)
    csv_path = output_dir / f"{task_id}.zip"
    error_path = output_dir / f"{task_id}.error"

    try:
        logger.debug(f"csv_export: Reading CSV from {csv_path}")
        df = pl.read_csv(csv_path)  # Will raise if file doesn't exist or unreadable

        logger.debug(f"csv_export: Creating CSV at {csv_path}")
        df.write_csv(csv_path)
        logger.info(f"zip_export: Successfully zipped to {csv_path}")
        return csv_path

    except Exception as e:
        logger.error(f"csv_export: Failed to export CSV to csv for {task_id}: {e}")
        error_path.write_text(f"An error occurred during csv export: {e}")
        raise
