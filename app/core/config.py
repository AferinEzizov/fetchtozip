"""

import json

with open("tutswiki.json", "r") as jsonfile:
    data = json.load(jsonfile)
    print("Read successful")
print(data)

"""


URL="/api/export"
DB_URL="http://localhost:3001/api/data"
TEMP_DIR='tmp'
INPUTS: list[INPUTS] = []
ADVANCED: list[ADVANCED] = []
