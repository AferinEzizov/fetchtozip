import requests
import polars as pl 

def fetch_data(url: str) -> pl.DataFrame: # url inputundan aldığı datanı  Polars Dataframi kimi return edir
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return pl.from_records(response.json())
