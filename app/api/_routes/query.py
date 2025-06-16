# app/api/_routes/input_management.py

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status
# Assuming app.core.schemas.input_schema and Input are correctly defined
from app.core.schemas.input_schema import Input, Configure
from app.core.config import Inputs, Configures

# Initialize an APIRouter instance for input management
router = APIRouter()

# In-memory input storage (consider a database for persistence in a real application)


logger = logging.getLogger(__name__)

@router.post("/inputs", summary="Add or update a single column input")
async def add_or_update_input(input_data: Input) -> Dict[str, Any]:
    """
    Adds a new input or updates an existing one in the in-memory list.
    The input is provided as a single JSON object in the request body.

    Args:
        input_data (Input): The input data to add/update, conforming to the Input schema.

    Returns:
        Dict[str, Any]: A message indicating success and the added/updated input.

    Raises:
        HTTPException: If there's an issue with the input data.
    """
    try:
        Inputs.append(input_data)
        logger.debug(f"Added single input: {input_data}")
        return {"message": "Single input added successfully", "input": input_data.dict()}
    except Exception as e:
        logger.error(f"Failed to add single input: {e}")
        # FastAPI's Pydantic validation handles most format errors automatically,
        # but this catch-all is good for unexpected issues.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid input format: {e}")

@router.post("/bulk-inputs", summary="Add multiple column inputs via JSON list")
async def add_bulk_inputs(inputs_data: List[Input]) -> Dict[str, Any]:
    """
    Adds multiple inputs to the in-memory list from a JSON array in the request body.

    Args:
        inputs_data (List[Input]): A list of input data items, each conforming to the Input schema.

    Returns:
        Dict[str, Any]: A message indicating success and the count of inputs added.

    Raises:
        HTTPException: If no inputs are provided or if there's an issue with the input format.
    """
    if not inputs_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No inputs provided in the list.")

    try:
        for input_item in inputs_data:
            Inputs.append(input_item)
        logger.debug(f"Added {len(inputs_data)} inputs in bulk.")
        return {"message": f"Successfully added {len(inputs_data)} inputs", "count_added": len(inputs_data)}
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
        "inputs": [i.dict() for i in Inputs],
        "count": len(Inputs)
    }

@router.post("/configure", summary="Configure how to process data and export it.")
async def configure_request(conf_data: Configure) -> Dict[str, Any]:
    """
    Adds a new config or updates an existing one in the in-memory list.
    The input is provided as a single JSON object in the request body.

    Args:
        conf_data (Configure): The config data to add/update, conforming to the Configure schema.

    Returns:
        Dict[str, Any]: A message indicating success and the added/updated Configures.

    Raises:
        HTTPException: If there's an issue with the config data.
    """
    try:
        Configures.clear()
        Configures.append(conf_data)
        logger.debug(f"Added single input: {conf_data}")
        return {"message": "Single input added successfully", "input": conf_data.dict()}
    except Exception as e:
        logger.error(f"Failed to add single input: {e}")
        # FastAPI's Pydantic validation handles most format errors automatically,
        # but this catch-all is good for unexpected issues.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid input format: {e}")
