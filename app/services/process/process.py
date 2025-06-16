from typing import List
from pathlib import Path
import polars as pl
from app.core.schemas.input_schema import Input
from app.core.config import TEMP_DIR

def rename_columns(df: pl.DataFrame, inputs: List[Input]) -> pl.DataFrame:
    rename_map = {}
    for input_data in inputs:
        if input_data.column is not None and input_data.name:
            if 0 <= input_data.column < len(df.columns):
                old_name = df.columns[input_data.column]
                rename_map[old_name] = input_data.name
    if rename_map:
        df = df.rename(rename_map)
    return df

def reorder_columns(df: pl.DataFrame, inputs: List[Input]) -> pl.DataFrame:
    # Build a mapping from original index to new order if change_order is specified
    index_to_new_order = {
        input_data.column: input_data.change_order
        for input_data in inputs
        if input_data.column is not None and input_data.change_order is not None
    }
    if not index_to_new_order:
        return df

    # Build the current column list
    columns = list(df.columns)
    # Build a list of (current_index, column_name, new_order or current_index)
    col_with_new_order = []
    for idx, col in enumerate(columns):
        new_order = index_to_new_order.get(idx, idx)
        col_with_new_order.append((new_order, col))
    # Sort columns by new_order
    col_with_new_order.sort()
    # Extract the reordered column names
    reordered_columns = [col for _, col in col_with_new_order]
    # Return DataFrame with reordered columns
    return df.select(reordered_columns)

def process(data: pl.LazyFrame, task_id: str, inputs: List[Input]) -> Path:
    """
    Processes a Polars LazyFrame by renaming columns and reordering columns
    based on provided inputs, then writes the resulting DataFrame to a CSV file
    in a temporary directory.

    Args:
        data: The input LazyFrame.
        task_id: A string identifier for the task, used in the output filename.
        inputs: A list of Input objects specifying column renaming and/or reordering.

    Returns:
        Path to the output CSV file.
    """
    df = data.collect()  # Collect the LazyFrame to an eager DataFrame

    # Apply renaming if needed
    if any(input_data.column is not None and input_data.name for input_data in inputs):
        df = rename_columns(df, inputs)

    # Apply reordering if needed
    if any(input_data.column is not None and input_data.change_order is not None for input_data in inputs):
        df = reorder_columns(df, inputs)

    output_path = Path(TEMP_DIR) / f"{task_id}.csv"
    df.write_csv(output_path)
    return output_path
