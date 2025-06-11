import polars as pl
from polars import col
from typing import List, NamedTuple

class INPUTS(NamedTuple):
    name: str
    change_order: int | None

def manipulate(df: pl.DataFrame, inputs: List[INPUTS]) -> pl.DataFrame:
    total_cols = len(df.columns)
    
    rename_map = {}
    move_map = {}

    for item in inputs:
        if item.change_order is not None and 0 <= item.change_order < total_cols:
            old_name = df.columns[item.change_order]
            rename_map[old_name] = item.name
            move_map[item.name] = item.change_order

    if not rename_map:
        raise ValueError("No valid column specifications found in the inputs.")

    # 1. Adlarını dəyiş (rename)
    df = df.rename(rename_map)

    # 2. Sıra düzəlişi üçün hazırla
    current_cols = df.columns
    reordered_cols = current_cols[:]  # copy

    for new_name, new_pos in move_map.items():
        reordered_cols.remove(new_name)
        reordered_cols.insert(new_pos, new_name)

    # 3. Sıralama ilə yeni DataFrame
    return df.select([col(c) for c in reordered_cols])
