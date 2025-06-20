import logging
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from typing import List

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    """
    Manages all active WebSocket connections. It allows new connections to be
    accepted and stored, disconnected connections to be removed, and messages
    to be broadcast to all connected clients.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Accepts a new WebSocket connection and adds it to the list of active connections.
        Logs the client's connection information.

        Args:
            websocket (WebSocket): The new WebSocket connection.
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected from client: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        """
        Removes a WebSocket connection from the active list.
        Logs the client's disconnection information.

        Args:
            websocket (WebSocket): The WebSocket connection to remove.
        """
        try:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected from client: {websocket.client}")
        except ValueError:
            logger.warning(f"Attempted to disconnect non-existent WebSocket: {websocket.client}. Connection already removed or not found.")


    async def broadcast(self, message: str):
        """
        Sends a text message to all active WebSocket clients.
        If a client connection fails, it is automatically disconnected.

        Args:
            message (str): The message string to send.
        """
        disconnected_websockets = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e: # Catch broad exceptions for connection issues
                logger.warning(f"Failed to send message to WebSocket client {connection.client}: {e}. Disconnecting.", exc_info=True)
                disconnected_websockets.append(connection)
        
        # Remove disconnected websockets after iterating to avoid modifying list during iteration
        for ws_to_remove in disconnected_websockets:
            self.disconnect(ws_to_remove) # Use the safe disconnect method
        logger.debug(f"Broadcasted message: '{message}'. Disconnected {len(disconnected_websockets)} clients during broadcast.")


# Global instance of the connection manager.
# This ensures all parts of the application share the same set of active connections.
manager = ConnectionManager()


@router.websocket(
    "/ws/notify",
)
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for clients to connect and receive live notifications about task progress.
    The connection is kept alive by continuously receiving (and discarding) messages,
    which also allows detection of client-initiated disconnects.
    """
    await manager.connect(websocket)
    try:
        # Keep the connection alive. This loop will run until the client disconnects or an error occurs.
        while True:
            # We don't necessarily expect messages *from* the client for notification purposes,
            # but receiving is necessary to keep the connection open and detect disconnects.
            # A timeout mechanism could be added here if no messages are expected for long periods.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket connection for {websocket.client} gracefully disconnected.")
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket connection for {websocket.client}: {e}", exc_info=True)
        manager.disconnect(websocket)


# ---- Public notification helpers ----

async def notify_download_processing(task_id: str):
    """
    Notifies all connected WebSocket clients that a download task is being processed.

    Args:
        task_id (str): The ID of the task being processed.
    """
    message = f"Download processing for task {task_id}"
    await manager.broadcast(message)

async def notify_download_start(task_id: str):
    """
    Notifies all connected WebSocket clients that a download task has started.

    Args:
        task_id (str): The ID of the task that has started downloading.
    """
    message = f"Download started for task {task_id}"
    await manager.broadcast(message)

async def notify_download_end(task_id: str):
    """
    Notifies all connected WebSocket clients that a download task has finished.

    Args:
        task_id (str): The ID of the task that has finished downloading.
    """
    message = f"Download finished for task {task_id}"
    await manager.broadcast(message)
