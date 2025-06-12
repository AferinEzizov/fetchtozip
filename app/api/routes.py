from fastapi import APIRouter
from app.api._routes import process, query, websocket

# Main API router
router = APIRouter()

# Register route modules with prefixes and tags
router.include_router(query.router, prefix="/api/export", tags=["Query"])
router.include_router(process.router, prefix="/api/export", tags=["Process"])
#router.include_router(websocket.router, prefix="/api/export/ws", tags=["WebSocket"])
