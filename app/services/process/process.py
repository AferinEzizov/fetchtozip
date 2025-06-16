from typing import List
from pathlib import Path
import polars as pl
from app.core.schemas.input_schema import Input
from app.core.config import TEMP_DIR


def process(data: pl.LazyFrame, task_id: str, inputs: List[Input]) -> Path:
    df = data.collect()  # eager for rename

    for input_data in inputs:
        if input_data.column is not None and input_data.name:
            if 0 <= input_data.column < len(df.columns):
                old_name = df.columns[input_data.column]
                df = df.rename({old_name: input_data.name})

    output_path = Path(TEMP_DIR) / f"{task_id}.csv"
    df.write_csv(output_path)
    return output_path
