import polars as pl
from pathlib import Path
from app.core.config import TEMP_DIR
import os
import logging

logger = logging.getLogger(__name__)

def json_export(json_path: Path, task_id: str) -> Path:
    output_dir = Path(TEMP_DIR)
    json_path = output_dir / f"{task_id}.json"
    error_path = output_dir / f"{task_id}.error"

    try:
        logger.debug(f"json_export: Reading JSON from {json_path}")
        df = pl.read_json(json_path)  # Will raise if file doesn't exist or unreadable

        logger.debug(f"json_export: Creating JSOON at {json_path}")
        df.write_ndjson(json_path)
        logger.info(f"json_export: Successfully wrote to {json_path}")
        return json_path

    except Exception as e:
        logger.error(f"json_export: Failed to export CSV to json for {task_id}: {e}")
        error_path.write_text(f"An error occurred during json export: {e}")
        raise

    finally:
        if json_path.exists():
            logger.debug(f"json_export: Cleaning up temporary JSON at {json_path}")
            os.remove(json_path)
