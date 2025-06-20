from fastapi import APIRouter

# Import all individual routers from submodules
from app.api._routes import db_query            # Manages DB connection configs
from app.api._routes import download           # Handles file downloads
from app.api._routes import query              # Manages Input and Configure objects
from app.api._routes import websocket          # Provides WebSocket notifications
from app.api._routes import table              # Fetches raw table data as JSON
from app.api._routes import pipeline_trigger   # Triggers the data processing pipeline (NEW)

# Main API router instance
router = APIRouter()

# Register route modules with prefixes and tags
# The prefixes create logical groups for the API endpoints (e.g., /api/config, /api/db_management).
# The tags are used by OpenAPI (Swagger UI) to categorize and organize the API documentation.

# Endpoints for managing Input objects (column transformations) and Configure objects (app settings)
router.include_router(query.router, prefix="/config", tags=["API Configuration"])

# Endpoints for managing external and local DB connection configurations
router.include_router(db_query.router, prefix="/db_management", tags=["Database Management"])

# Endpoints for fetching raw table data as JSON
router.include_router(table.router, prefix="/tables", tags=["Table Data Retrieval"])

# Endpoints for WebSocket notifications
router.include_router(websocket.router, prefix="/notifications", tags=["WebSocket Notifications"])

# Endpoints for file downloads
router.include_router(download.router, prefix="/downloads", tags=["File Download"])

# NEW: Endpoint to trigger the full data processing pipeline
router.include_router(pipeline_trigger.router, prefix="/pipeline", tags=["Data Processing Pipeline"])
