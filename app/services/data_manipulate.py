import polars as pl
from polars import col
from typing import List, NamedTuple # Or dataclasses, Pydantic models, etc.

class INPUTS(NamedTuple):
    name: str
    change_order: int | None

def manipulate(df: pl.DataFrame, inputs: List[INPUTS]) -> pl.DataFrame:
    total_cols = len(df.columns)
    
    cols_to_process = []
    for item in inputs:
        if item.change_order is not None and 0 <= item.change_order < total_cols:
            original_col_name = df.columns[item.change_order]
            
            cols_to_process.append({
                "order": item.change_order,
                "original_name": original_col_name,
                "new_name": item.name
            })
            
    if not cols_to_process:
        raise ValueError("No valid column specifications found in the inputs.")
        
    cols_to_process.sort(key=lambda x: x["order"])
    
    select_expressions = [
        col(spec["original_name"]).alias(spec["new_name"]) for spec in cols_to_process
    ]
    
    return df.select(select_expressions)

if __name__ == '__main__':
    sample_df = pl.DataFrame({
        "first_col": [1, 2, 3],
        "second_col": ["a", "b", "c"],
        "third_col": [True, False, True],
    })

    my_inputs = [
        INPUTS(name="result", change_order=2),
        INPUTS(name="identifier", change_order=0),
        INPUTS(name="unused_col", change_order=1), # This will be used to demonstrate renaming
    ]
    
    all_inputs = [
        INPUTS(name="ID", change_order=0),
        INPUTS(name="Category", change_order=1),
        INPUTS(name="Flag", change_order=2),
    ]


    try:
        final_df = manipulate(sample_df, all_inputs)

        print("Original DataFrame:")
        print(sample_df)
        print("\nManipulated DataFrame:")
        print(final_df)

    except ValueError as e:
        print(f"An error occurred: {e}")

