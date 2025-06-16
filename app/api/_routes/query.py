import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status

# Assuming app.core.schemas.input_schema and Input, Configure are correctly defined
# IMPORTANT: This import assumes your Input and Configure models are in a file
# like app/core/schemas/input_schema.py. If they are directly in app/core/config.py
# as in your previous prompt, you would import them from there.
from app.core.schemas.input_schema import Input, Configure
# from app.core.config import Input, Configure # Use this if models are in config.py directly

from app.core.config import Inputs, Configures # These are your in-memory lists

# Initialize an APIRouter instance for input management
router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/inputs", summary="Add or update a single column input")
async def add_or_update_input(input_data: Input): # Corrected to handle a single Input object
    """
    Adds a new input or updates an existing one in the in-memory list.
    The input is provided as a single JSON object in the request body.

    Args:
        input_data (Input): The input data to add/update, conforming to the Input schema.
                            It's expected to have a 'name' field for identification.

    Returns:
        Dict[str, Any]: A message indicating success and the added/updated input.

    Raises:
        HTTPException: If there's an issue with the input data or if 'name' is missing.
    """
    if input_data.name is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input 'name' is required for adding or updating a single input."
        )

    try:
        found = False
        # Iterate through existing inputs to find a match by 'name'
        for i, existing_input in enumerate(Inputs):
            if existing_input.name == input_data.name:
                Inputs[i] = input_data # Update the existing input
                found = True
                logger.debug(f"Updated input: {input_data.name}")
                break

        if not found:
            Inputs.append(input_data) # Add as a new input if not found
            logger.debug(f"Added new input: {input_data.name}")

        # Use .model_dump() for Pydantic v2 compatibility
        return {"message": "Input added/updated successfully", "input": input_data.model_dump()}
    except Exception as e:
        logger.error(f"Failed to add/update single input: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid input format: {e}")

@router.post("/bulk-inputs", summary="Add multiple column inputs via JSON list")
async def add_bulk_inputs(inputs_data: List[Input]) :
    """
    Adds multiple inputs to the in-memory list from a JSON array in the request body.
    Existing inputs with the same 'name' will be updated.

    Args:
        inputs_data (List[Input]): A list of input data items, each conforming to the Input schema.

    Returns:
        Dict[str, Any]: A message indicating success and the count of inputs added/updated.

    Raises:
        HTTPException: If no inputs are provided or if there's an issue with the input format.
    """
    if not inputs_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No inputs provided in the list.")

    added_count = 0
    updated_count = 0
    try:
        for input_item in inputs_data:
            if input_item.name is None:
                logger.warning(f"Skipping input due to missing 'name': {input_item}")
                continue # Skip inputs without a name, or raise an error

            found = False
            for i, existing_input in enumerate(Inputs):
                if existing_input.name == input_item.name:
                    Inputs[i] = input_item # Update existing
                    found = True
                    updated_count += 1
                    break
            if not found:
                Inputs.append(input_item) # Add new
                added_count += 1

        logger.debug(f"Bulk operation: Added {added_count}, Updated {updated_count} inputs.")
        return {
            "message": f"Successfully added {added_count} and updated {updated_count} inputs",
            "added_count": added_count,
            "updated_count": updated_count
        }
    except Exception as e:
        logger.error(f"Failed to add bulk inputs: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid bulk input format: {e}")

@router.delete("/inputs-clear", summary="Clear all stored inputs")
async def clear_all_inputs() -> Dict[str, str]:
    """
    Clears all input data currently stored in memory.

    Returns:
        Dict[str, str]: A success message.
    """
    Inputs.clear()
    logger.debug("All inputs cleared.")
    return {"message": "All inputs cleared"}

@router.get("/inputs-list", summary="List all stored inputs")
async def get_all_inputs() -> Dict[str, Any]:
    """
    Retrieves a list of all input data currently stored in memory.

    Returns:
        Dict[str, Any]: A dictionary containing the list of inputs and their count.
    """
    logger.debug(f"Listing {len(Inputs)} inputs.")
    return {
        "inputs": [i.model_dump() for i in Inputs], # Use .model_dump() for Pydantic v2
        "count": len(Inputs)
    }

@router.post("/configure", summary="Set the active data processing and export configuration") # Improved summary
async def configure_request(conf_data: Configure) -> Dict[str, Any]:
    """
    Sets the active configuration for data processing and export.
    This replaces any previously stored configuration with the new one.

    Args:
        conf_data (Configure): The configuration data, conforming to the Configure schema.

    Returns:
        Dict[str, Any]: A message indicating success and the new active configuration.

    Raises:
        HTTPException: If there's an issue with the config data.
    """
    try:
        Configures.clear() # Clears previous configurations
        Configures.append(conf_data) # Adds the new configuration as the sole active one
        logger.debug(f"Active configuration set: {conf_data}")
        # Use .model_dump() for Pydantic v2 compatibility
        return {"message": "Configuration set successfully", "configuration": conf_data.model_dump()}
    except Exception as e:
        logger.error(f"Failed to set configuration: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid configuration format: {e}")
