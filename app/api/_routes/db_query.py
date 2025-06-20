import logging
from typing import Dict, Any, List, Union
from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from app.core.schemas.input_schema import ExternalDBSchema, LocalDBSchema

router = APIRouter()
logger = logging.getLogger(__name__)

# --- In-memory stores for DB configurations ---
# These global lists will hold the actual Pydantic models for DB configs managed via API.
# They are separate from any configurations loaded from config.json (which serves as default).
_IN_MEMORY_EXTERNAL_DB_CONFIGS: List[ExternalDBSchema] = []
_IN_MEMORY_LOCAL_DB_CONFIGS: List[LocalDBSchema] = []


@router.post("/db/external", summary="Add or update an external DB configuration", response_model=Dict[str, Any])
async def add_or_update_external_db_config(db_data: ExternalDBSchema) -> Dict[str, Any]:
    """
    Adds a new external database configuration or updates an existing one in the in-memory store.
    The unique identifier for an external DB config is a composite key: `db_type`, `host`, `db_name`.

    Args:
        db_data (ExternalDBSchema): A fully populated ExternalDBSchema object.

    Returns:
        Dict[str, Any]: Confirmation message and the details of the added/updated DB config.

    Raises:
        HTTPException (400 Bad Request): If an error occurs during the add/update operation.
    """
    # Create a unique key for the external DB configuration
    key = f"{db_data.db_type}_{db_data.host}_{db_data.db_name}"
    try:
        global _IN_MEMORY_EXTERNAL_DB_CONFIGS
        found = False
        for i, existing_db_schema in enumerate(_IN_MEMORY_EXTERNAL_DB_CONFIGS):
            existing_key = f"{existing_db_schema.db_type}_{existing_db_schema.host}_{existing_db_schema.db_name}"
            if existing_key == key:
                _IN_MEMORY_EXTERNAL_DB_CONFIGS[i] = db_data # Update the existing entry
                found = True
                logger.info(f"Updated external DB config for key: '{key}'")
                break
        if not found:
            _IN_MEMORY_EXTERNAL_DB_CONFIGS.append(db_data) # Add new entry
            logger.info(f"Added new external DB config for key: '{key}'")

        # Use model_dump() for serialization; SecretStr handles password masking.
        return {
            "message": "External DB config added/updated successfully",
            "db_config": db_data.model_dump()
        }
    except Exception as e:
        logger.error(f"Failed to add/update external DB config for key '{key}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add/update external DB config: {e}"
        )

@router.post("/db/local", summary="Add or update a local SQLite DB configuration", response_model=Dict[str, Any])
async def add_or_update_local_db_config(db_data: LocalDBSchema) -> Dict[str, Any]:
    """
    Adds a new local SQLite database configuration or updates an existing one in the in-memory store.
    The unique identifier for a local DB config is its `db_file_path`.

    Args:
        db_data (LocalDBSchema): A fully populated LocalDBSchema object.

    Returns:
        Dict[str, Any]: Confirmation message and the details of the added/updated DB config.

    Raises:
        HTTPException (400 Bad Request): If an error occurs during the operation.
    """
    key = db_data.db_file_path # Use db_file_path as the unique key for local DBs
    try:
        global _IN_MEMORY_LOCAL_DB_CONFIGS
        found = False
        for i, existing_db_schema in enumerate(_IN_MEMORY_LOCAL_DB_CONFIGS):
            if existing_db_schema.db_file_path == key:
                _IN_MEMORY_LOCAL_DB_CONFIGS[i] = db_data # Update the existing entry
                found = True
                logger.info(f"Updated local DB config for path: '{key}'")
                break
        if not found:
            _IN_MEMORY_LOCAL_DB_CONFIGS.append(db_data) # Add new entry
            logger.info(f"Added new local DB config for path: '{key}'")

        return {
            "message": "Local DB config added/updated successfully",
            "db_config": db_data.model_dump()
        }
    except Exception as e:
        logger.error(f"Failed to add/update local DB config for path '{key}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add/update local DB config: {e}"
        )

@router.get("/db/list", summary="List all stored DB configurations", response_model=Dict[str, Any])
async def list_all_db_configs() -> Dict[str, Any]:
    """
    Retrieves a list of all database configurations (both external and local)
    currently stored in memory.

    Returns:
        Dict[str, Any]: A dictionary containing lists of external and local DB configs, and a total count.
    """
    logger.debug(f"Listing {len(_IN_MEMORY_EXTERNAL_DB_CONFIGS)} external and {len(_IN_MEMORY_LOCAL_DB_CONFIGS)} local DB configs.")
    return {
        "external_db_configs": [entry.model_dump() for entry in _IN_MEMORY_EXTERNAL_DB_CONFIGS],
        "local_db_configs": [entry.model_dump() for entry in _IN_MEMORY_LOCAL_DB_CONFIGS],
        "total_count": len(_IN_MEMORY_EXTERNAL_DB_CONFIGS) + len(_IN_MEMORY_LOCAL_DB_CONFIGS)
    }

@router.delete("/db/clear/external", summary="Clear all stored external DB configurations")
async def clear_external_db_configs() -> Dict[str, str]:
    """
    Clears all external database configurations currently stored in memory.

    Returns:
        Dict[str, str]: A success message.
    """
    global _IN_MEMORY_EXTERNAL_DB_CONFIGS
    _IN_MEMORY_EXTERNAL_DB_CONFIGS.clear()
    logger.info("All external DB configs cleared.")
    return {"message": "All external DB configurations cleared"}

@router.delete("/db/clear/local", summary="Clear all stored local DB configurations")
async def clear_local_db_configs() -> Dict[str, str]:
    """
    Clears all local SQLite database configurations currently stored in memory.

    Returns:
        Dict[str, str]: A success message.
    """
    global _IN_MEMORY_LOCAL_DB_CONFIGS
    _IN_MEMORY_LOCAL_DB_CONFIGS.clear()
    logger.info("All local DB configs cleared.")
    return {"message": "All local DB configurations cleared"}

@router.delete("/db/clear/all", summary="Clear all stored DB configurations (external and local)")
async def clear_all_db_configs_combined() -> Dict[str, str]:
    """
    Clears all database configurations (both external and local) currently stored in memory.

    Returns:
        Dict[str, str]: A success message.
    """
    global _IN_MEMORY_EXTERNAL_DB_CONFIGS, _IN_MEMORY_LOCAL_DB_CONFIGS
    _IN_MEMORY_EXTERNAL_DB_CONFIGS.clear()
    _IN_MEMORY_LOCAL_DB_CONFIGS.clear()
    logger.info("All DB configurations (external and local) cleared.")
    return {"message": "All DB configurations cleared"}
