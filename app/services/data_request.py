import requests
import polars as pl

def fetch_data(base_url: str, max_pages: int = 10, limit: int = 100) -> pl.DataFrame:
    all_data = []

    for page in range(1, max_pages + 1):
        url = f"{base_url}?page={page}&limit={limit}"
        response = requests.get(url)
        data = response.json()
        if not data:
            break
        all_data.extend(data)

    all_keys = set()
    for row in all_data:
        all_keys.update(row.keys())

    normalized_data = [
        {key: row.get(key, None) for key in all_keys}
        for row in all_data
    ]

    df = pl.DataFrame(normalized_data)

    numeric_cols = [col for col in df.columns if df[col].dtype in [pl.Float64, pl.Int64]]

    normalized_df = df.select([
        ((pl.col(col) - pl.col(col).min()) / (pl.col(col).max() - pl.col(col).min())).alias(col)
        for col in numeric_cols
    ] + [pl.col(col) for col in df.columns if col not in numeric_cols])

    return normalized_df

