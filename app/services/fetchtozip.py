import requests
import polars as polars
from pathlib import Path
from zipfile import ZipFile 
import logging


TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exits_ok=True)

SOURCE_URL = "http://localhost:8080/data.xlsx"


def p_fetchtozip(task_id: str):
    try:

        excel_path = TEMP_DIR / f"task_id.xlsx"
        response = requests.get(SOURCE_URL, timeout=10)
        respone.raise_for_status()
        excel_path.write_bytes(respone.content)
        
        df = pl.read_excel(excel_path)


        required_cols = {"Gender", "Age"}
        if not required_cols.issubset(set(df.columns)):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing columns: {missing}")

        df = df.rename({
                    "Gender": "Cinsiyyet"
                    "Age":"Yas"
                })
        df = df.select(["Cinsiyyet","Yas"])

        processed_path = TEMP_DIR / f"{task_id}_p.xlsx"
        df.write_excel(processed_path)

        zip_path = TEMP_DIR / f"{task_id}.zip"

        with ZipFile(zip_path, "w") as zipf:
            zipf.write(processed_path, arcname="data.xlsx")

    except Expception as e:
        ( TEMP_DIR / f"{task_id.error}".write_text(str(e)))
