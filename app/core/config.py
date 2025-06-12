import json
from pathlib import Path

# Load JSON config file
CONFIG_PATH = Path("app/core/json/config.json")

with CONFIG_PATH.open("r") as file:
    config = json.load(file)

# Static configuration variables
URL: str = config.get("URL", "")
DB_URL: str = config.get("DB_URL", "")
TEMP_DIR: str = config.get("TEMP_DIR", "tmp")
Inputs: dict = config.get("ADVANCED", {})
ADVANCED: dict = config.get("ADVANCED", {})
