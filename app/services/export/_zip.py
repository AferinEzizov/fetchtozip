import logging
from pathlib import Path
import zipfile
import shutil # For potential future file operations, not strictly used in current version

logger = logging.getLogger(__name__)

def zip_export(file_path: Path, task_id: str, output_dir: Path) -> Path:
    """
    Creates a zip archive containing the specified file within the given output directory.
    The original file at `file_path` is left untouched by this function;
    its deletion (if desired) should be handled by the caller.

    Args:
        file_path (Path): The path to the file to be zipped (e.g., the processed CSV).
        task_id (str): The ID of the task, used for naming the zip file.
        output_dir (Path): The directory where the zip file should be created.

    Returns:
        Path: The path to the created zip file.

    Raises:
        FileNotFoundError: If the file to be zipped does not exist.
        RuntimeError: If zipping fails due to other reasons.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File to zip not found: {file_path.resolve()}")

    # Ensure the output directory for the zip file exists
    output_dir.mkdir(parents=True, exist_ok=True)

    zip_file_name = f"{task_id}.zip"
    zip_output_path = output_dir / zip_file_name

    logger.info(f"Attempting to zip '{file_path.resolve()}' to '{zip_output_path.resolve()}'.")

    try:
        # Create a zip archive. `zipfile.ZIP_DEFLATED` specifies compression.
        with zipfile.ZipFile(zip_output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add the file to the zip archive. `arcname` defines its name inside the zip.
            # Using file_path.name ensures only the file name (not its full path) is inside the zip.
            zipf.write(file_path, arcname=file_path.name)

        logger.info(f"Successfully zipped '{file_path.name}' to '{zip_output_path.resolve()}'.")
        
        return zip_output_path
    except Exception as e:
        logger.error(f"Failed to create zip archive from '{file_path.resolve()}': {e}", exc_info=True)
        raise RuntimeError(f"Zip export failed: {e}") from e
