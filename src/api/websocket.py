import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.core.events import serialize_events, operation_events

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/operations")
async def watch_operations(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json(
        {
            "type": "welcome",
            "message": "WebSocket operation feed connected",
            "note": "This is a starter stream and can evolve with richer watch semantics.",
        }
    )

    last_id = 0
    try:
        while True:
            events = operation_events.list_since(last_id)
            if events:
                last_id = events[-1].id
                await websocket.send_json({"type": "events", "items": serialize_events(events)})
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return
