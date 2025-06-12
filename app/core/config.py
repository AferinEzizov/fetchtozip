import json

# Load JSON config
with open('config.json', 'r') as file:
    config = json.load(file)

# Assign variables from config
URL = config.get("URL", "")
DB_URL = config.get("DB_URL", "")
TEMP_DIR = config.get("TEMP_DIR", "")
INPUTS = config.get("INPUTS", [])
ADVANCED = config.get("ADVANCED", [])


