import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

# Import schemas
from app.core.schemas.input_schema import Input, Configure

router = APIRouter()
logger = logging.getLogger(__name__)

# --- In-memory stores for API-managed configurations ---
# These lists will hold the actual Pydantic models for Input and Configure objects.
# They are managed directly by this API module, providing a volatile in-memory state.
_IN_MEMORY_INPUTS: List[Input] = []
_ACTIVE_CONFIGURE: Optional[Configure] = None # Stores the single active Configure object


@router.post("/inputs", summary="Add or update a single column input", response_model=Dict[str, Any])
async def add_or_update_input(input_data: Input) -> Dict[str, Any]:
    """
    Adds a new column transformation input or updates an existing one in the in-memory list.
    The input is identified by its `name` field.

    Args:
        input_data (Input): The input data to add/update, conforming to the Input schema.
                            The 'name' field is used as a unique identifier.

    Returns:
        Dict[str, Any]: A message indicating success and the details of the added/updated input.

    Raises:
        HTTPException (400 Bad Request): If 'name' is missing from input_data or on other processing errors.
    """
    if input_data.name is None:
        logger.warning("Attempted to add/update single input with missing 'name' field.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input 'name' is required for adding or updating a single input."
        )

    try:
        global _IN_MEMORY_INPUTS
        found = False
        for i, existing_input in enumerate(_IN_MEMORY_INPUTS):
            if existing_input.name == input_data.name:
                _IN_MEMORY_INPUTS[i] = input_data # Update the existing input
                found = True
                logger.info(f"Updated input for name: '{input_data.name}'")
                break

        if not found:
            _IN_MEMORY_INPUTS.append(input_data) # Add as a new input if not found
            logger.info(f"Added new input for name: '{input_data.name}'")

        return {"message": "Input added/updated successfully", "input": input_data.model_dump()}
    except Exception as e:
        logger.error(f"Failed to add/update single input '{input_data.name}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid input data: {e}")


@router.post("/inputs/bulk", summary="Add multiple column inputs via JSON list", response_model=Dict[str, Any])
async def add_bulk_inputs(inputs_data: List[Input]) -> Dict[str, Any]:
    """
    Adds multiple column transformation inputs to the in-memory list from a JSON array.
    Existing inputs with the same 'name' will be updated.

    Args:
        inputs_data (List[Input]): A list of input data items, each conforming to the Input schema.

    Returns:
        Dict[str, Any]: A message indicating success, and counts of added/updated inputs.

    Raises:
        HTTPException (400 Bad Request): If no inputs are provided or if there's an issue with the input format.
    """
    if not inputs_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No inputs provided in the list.")

    added_count = 0
    updated_count = 0
    try:
        global _IN_MEMORY_INPUTS
        for input_item in inputs_data:
            if input_item.name is None:
                logger.warning(f"Skipping bulk input item due to missing 'name' field: {input_item.model_dump_json()}.")
                continue # Skip inputs without a name

            found = False
            for i, existing_input in enumerate(_IN_MEMORY_INPUTS):
                if existing_input.name == input_item.name:
                    _IN_MEMORY_INPUTS[i] = input_item # Update existing
                    found = True
                    updated_count += 1
                    break
            if not found:
                _IN_MEMORY_INPUTS.append(input_item) # Add new
                added_count += 1

        logger.info(f"Bulk input operation completed: Added {added_count}, Updated {updated_count} inputs.")
        return {
            "message": f"Successfully added {added_count} and updated {updated_count} inputs",
            "added_count": added_count,
            "updated_count": updated_count
        }
    except Exception as e:
        logger.error(f"Failed to add bulk inputs: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid bulk input format: {e}")


@router.delete("/inputs/clear", summary="Clear all stored inputs", response_model=Dict[str, str])
async def clear_all_inputs() -> Dict[str, str]:
    """
    Clears all column transformation input data currently stored in memory.

    Returns:
        Dict[str, str]: A success message.
    """
    global _IN_MEMORY_INPUTS
    _IN_MEMORY_INPUTS.clear()
    logger.info("All inputs cleared.")
    return {"message": "All inputs cleared"}


@router.get("/inputs/list", summary="List all stored inputs", response_model=Dict[str, Any])
async def get_all_inputs() -> Dict[str, Any]:
    """
    Retrieves a list of all column transformation input data currently stored in memory.

    Returns:
        Dict[str, Any]: A dictionary containing the list of inputs and their count.
    """
    logger.debug(f"Listing {len(_IN_MEMORY_INPUTS)} inputs.")
    return {
        "inputs": [i.model_dump() for i in _IN_MEMORY_INPUTS],
        "count": len(_IN_MEMORY_INPUTS)
    }


@router.post("/configure", summary="Set the active data processing and export configuration", response_model=Dict[str, Any])
async def configure_request(conf_data: Configure) -> Dict[str, Any]:
    """
    Sets the active configuration for data processing and export.
    This replaces any previously stored configuration with the new one,
    ensuring only one active configuration at a time.

    Args:
        conf_data (Configure): The configuration data, conforming to the Configure schema.

    Returns:
        Dict[str, Any]: A message indicating success and the new active configuration.

    Raises:
        HTTPException (400 Bad Request): If there's an issue with the config data.
    """
    try:
        global _ACTIVE_CONFIGURE
        _ACTIVE_CONFIGURE = conf_data # Set the new active configuration
        logger.info(f"Active application configuration set: {_ACTIVE_CONFIGURE.model_dump_json()}")
        return {"message": "Configuration set successfully", "configuration": _ACTIVE_CONFIGURE.model_dump()}
    except Exception as e:
        logger.error(f"Failed to set configuration: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid configuration format: {e}")

@router.get("/configure/active", summary="Get the active application configuration", response_model=Dict[str, Any])
async def get_active_configuration() -> Dict[str, Any]:
    """
    Retrieves the currently active application configuration.

    Returns:
        Dict[str, Any]: A dictionary containing the active configuration, or a message if none is set.
    """
    global _ACTIVE_CONFIGURE
    if _ACTIVE_CONFIGURE:
        logger.debug("Returning active application configuration.")
        return {"message": "Active configuration retrieved successfully", "configuration": _ACTIVE_CONFIGURE.model_dump()}
    else:
        logger.info("No active application configuration set. Returning default (if available).")
        # Optionally, you could return DEFAULT_APP_CONFIGURE from app.core.config here
        # if no API-set active config exists. For simplicity, just indicate no active.
        return {"message": "No active configuration set via API.", "configuration": None}
