from fastapi import WebSocket, WebSocketDisconnect, APIRouter

router = APIRouter()


class ConnectionManager:
    """
    Manages all active WebSocket connections and
    allows broadcasting messages to all of them.
    """
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Accepts and stores a new WebSocket connection.
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Removes a disconnected WebSocket.
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        """
        Sends a message to all active WebSocket clients.
        """
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                self.disconnect(connection)


# Global instance of the connection manager
manager = ConnectionManager()


@router.websocket(
    "/ws/notify",
)
async def websocket_endpoint(websocket: WebSocket):
    """
    Clients connect here to receive live notifications about download tasks.

    Messages sent:
    - Download processing for task {task_id}
    - Download started for task {task_id}
    - Download finished for task {task_id}

    The server keeps the connection open and pushes events in real time.
    """
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ---- Public notification helpers ----

async def notify_download_processing(task_id: str):
    """
    Notify all clients that a download is being processed.
    """
    await manager.broadcast(f" Download processing for task {task_id}")


async def notify_download_start(task_id: str):
    """
    Notify all clients that a download has started.
    """
    await manager.broadcast(f" Download started for task {task_id}")


async def notify_download_end(task_id: str):
    """
    Notify all clients that a download has finished.
    """
    await manager.broadcast(f" Download finished for task {task_id}")

