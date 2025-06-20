import logging
from typing import List, Dict, Any
from pathlib import Path

import polars as pl

from app.core.schemas.input_schema import Input
from app.core.config import TEMP_DIR # TEMP_DIR is now consistently a Path object

logger = logging.getLogger(__name__)

def rename_columns(df: pl.DataFrame, inputs: List[Input]) -> pl.DataFrame:
    """
    Renames columns in a Polars DataFrame based on provided input specifications.

    Args:
        df (pl.DataFrame): The input Polars DataFrame.
        inputs (List[Input]): A list of Input objects, each potentially specifying
                              a column index and a new name for that column.

    Returns:
        pl.DataFrame: The DataFrame with columns renamed.
    """
    rename_map: Dict[str, str] = {}
    for input_data in inputs:
        col_idx = input_data.column
        new_name = input_data.name

        if col_idx is not None and new_name:
            if 0 <= col_idx < len(df.columns):
                old_name = df.columns[col_idx]
                if old_name in rename_map:
                    logger.warning(
                        f"Rename conflict: Column '{old_name}' (index {col_idx}) is targeted multiple times. "
                        f"Last specification to rename to '{new_name}' will apply."
                    )
                rename_map[old_name] = new_name
                logger.debug(f"Queued rename: Column '{old_name}' (index {col_idx}) to '{new_name}'")
            else:
                logger.warning(
                    f"Rename skipped: Column index {col_idx} out of bounds for DataFrame with {len(df.columns)} columns."
                )
    
    if rename_map:
        logger.info(f"Applying column renames: {rename_map}")
        df = df.rename(rename_map)
    else:
        logger.info("No column renames specified or applicable.")
    return df

def reorder_columns(df: pl.DataFrame, inputs: List[Input]) -> pl.DataFrame:
    """
    Reorders columns in a Polars DataFrame based on provided input specifications.
    Columns not explicitly specified for reordering will maintain their original relative positions.

    Args:
        df (pl.DataFrame): The input Polars DataFrame.
        inputs (List[Input]): A list of Input objects, each potentially specifying
                              a column index and its new position (`change_order`).

    Returns:
        pl.DataFrame: The DataFrame with columns reordered.
    """
    index_to_new_order: Dict[int, int] = {}
    for input_data in inputs:
        col_idx = input_data.column
        new_order = input_data.change_order

        if col_idx is not None and new_order is not None:
            if 0 <= col_idx < len(df.columns):
                # Clamp new_order to be within valid bounds of the current column count
                clamped_new_order = max(0, min(new_order, len(df.columns) - 1))
                if new_order != clamped_new_order:
                    logger.warning(
                        f"Reorder position {new_order} for column '{df.columns[col_idx]}' (index {col_idx}) is out of "
                        f"bounds ({len(df.columns)} columns). Clamping to {clamped_new_order}."
                    )

                if col_idx in index_to_new_order:
                    logger.warning(
                        f"Reorder conflict: Column '{df.columns[col_idx]}' (index {col_idx}) is targeted multiple times. "
                        f"Last specification to order to position {clamped_new_order} will apply."
                    )
                index_to_new_order[col_idx] = clamped_new_order
                logger.debug(f"Queued reorder: Column '{df.columns[col_idx]}' (index {col_idx}) to position {clamped_new_order}")
            else:
                logger.warning(
                    f"Reorder skipped: Column index {col_idx} out of bounds for DataFrame with {len(df.columns)} columns."
                )

    if not index_to_new_order:
        logger.info("No column reordering specified or applicable.")
        return df

    current_columns = list(df.columns)
    final_ordered_columns = [None] * len(current_columns)

    # Step 1: Place explicitly reordered columns
    placed_original_indices = set()
    for original_idx, target_pos in index_to_new_order.items():
        if target_pos < len(final_ordered_columns):
            if final_ordered_columns[target_pos] is not None:
                logger.warning(
                    f"Reorder position {target_pos} is already occupied by '{final_ordered_columns[target_pos]}'. "
                    f"Overwriting with '{current_columns[original_idx]}'."
                )
            final_ordered_columns[target_pos] = current_columns[original_idx]
            placed_original_indices.add(original_idx)
        else:
            logger.warning(
                f"Skipping reorder of column '{current_columns[original_idx]}' (index {original_idx}) "
                f"to invalid position {target_pos} as it's beyond DataFrame size."
            )

    # Step 2: Fill remaining slots with non-reordered columns, maintaining original relative order
    original_column_cursor = 0
    for i in range(len(final_ordered_columns)):
        if final_ordered_columns[i] is None:
            while original_column_cursor < len(current_columns) and \
                  original_column_cursor in placed_original_indices:
                original_column_cursor += 1

            if original_column_cursor < len(current_columns):
                final_ordered_columns[i] = current_columns[original_column_cursor]
                placed_original_indices.add(original_column_cursor)
                original_column_cursor += 1
            
    reordered_columns_names = [col_name for col_name in final_ordered_columns if col_name is not None]

    if len(reordered_columns_names) != len(current_columns):
        logger.error(
            f"Column reordering resulted in an incorrect number of columns. "
            f"Expected {len(current_columns)}, got {len(reordered_columns_names)}. "
            "This indicates a logical error in reordering or invalid input parameters."
        )

    logger.info(f"Applying column reordering: Final column order: {reordered_columns_names}")
    return df.select(reordered_columns_names)


def process(data: pl.LazyFrame, task_id: str, inputs: List[Input]) -> Path:
    """
    Collects a LazyFrame, applies column renaming and reordering based on inputs,
    and saves the processed data to a temporary CSV file within the global TEMP_DIR.

    Args:
        data (pl.LazyFrame): The input data as a Polars LazyFrame.
        task_id (str): A unique identifier for the task, used for the output filename.
        inputs (List[Input]): A list of Input objects specifying column transformations.

    Returns:
        Path: The file path to the saved CSV output.

    Raises:
        ValueError: If `data` is not a Polars LazyFrame.
        RuntimeError: If data collection or saving fails.
    """
    if not isinstance(data, pl.LazyFrame):
        raise ValueError(f"Expected input 'data' to be a Polars LazyFrame, but got {type(data).__name__}.")

    logger.info(f"Initiating data processing for task_id='{task_id}'.")
    
    try:
        df = data.collect()
        logger.debug(f"LazyFrame collected into DataFrame for task_id='{task_id}'. Rows: {df.shape[0]}, Cols: {df.shape[1]}")
    except pl.ComputeError as e:
        logger.error(f"Failed to collect LazyFrame for task_id='{task_id}': {e}", exc_info=True)
        raise RuntimeError(f"Error collecting data for processing: {e}") from e

    if df.is_empty():
        logger.warning(f"DataFrame is empty after collection for task_id='{task_id}'. No transformations will be applied.")

    # Apply renaming operations if specified
    needs_rename = any(input_data.column is not None and input_data.name for input_data in inputs)
    if needs_rename:
        df = rename_columns(df, inputs)
    else:
        logger.debug(f"No renaming operations specified for task_id='{task_id}'.")

    # Apply reordering operations if specified
    needs_reorder = any(input_data.column is not None and input_data.change_order is not None for input_data in inputs)
    if needs_reorder:
        df = reorder_columns(df, inputs)
    else:
        logger.debug(f"No reordering operations specified for task_id='{task_id}'.")

    # Define the output path within the global TEMP_DIR
    output_path: Path = TEMP_DIR / f"{task_id}.csv"
    
    try:
        df.write_csv(output_path)
        logger.info(f"Processed data (CSV) saved to {output_path.resolve()}")
    except Exception as e:
        logger.error(f"Failed to write processed data to CSV for task_id='{task_id}': {e}", exc_info=True)
        raise RuntimeError(f"Failed to save processed data to CSV: {e}") from e
        
    return output_path
