from pathlib import Path
TEMP_DIR = Path("temp") # Configə daxil ediləcək
TEMP_DIR.mkdir(exist_ok=True)
INPUT = [None, None, "default_column_name", 0] # INPUT[3] initialized as int

SOURCE_URL = "http://127.0.0.1:8080/data.xlsx" # Configə daxil ediləcək
