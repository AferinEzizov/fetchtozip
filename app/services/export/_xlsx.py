import polars as pl
from pathlib import Path
from app.core.config import TEMP_DIR
import os
import logging

logger = logging.getLogger(__name__)

def xlsx_export(xlsx_path: Path, task_id: str) -> Path:
    output_dir = Path(TEMP_DIR)
    xlsx_path = output_dir / f"{task_id}.xlsx"
    error_path = output_dir / f"{task_id}.error"

    try:
        logger.debug(f"xlsx_export: Reading XLSX from {xlsx_path}")
        df = pl.read_excel(xlsx_path)  # Will raise if file doesn't exist or unreadable

        logger.debug(f"xlsx_export: Creating XLSX at {xlsx_path}")
        df.write_excel(xlsx_path)
        logger.info(f"xlsx_export: Successfully wrote to {xlsx_path}")
        return xlsx_path

    except Exception as e:
        logger.error(f"xlsx_export: Failed to export to xlsx for {task_id}: {e}")
        error_path.write_text(f"An error occurred during xlsx export: {e}")
        raise

    finally:
        if xlsx_path.exists():
            logger.debug(f"xlsx_export: Cleaning up temporary XLSX at {xlsx_path}")
            os.remove(xlsx_path)
