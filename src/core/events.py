from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any


@dataclass
class OperationEvent:
    id: int
    ts: str
    layer: str
    operation: str
    status: str
    payload: dict[str, Any]


class OperationEventStore:
    def __init__(self) -> None:
        self._events: list[OperationEvent] = []
        self._next_id = 1
        self._lock = Lock()

    def record(self, layer: str, operation: str, status: str, payload: dict[str, Any]) -> OperationEvent:
        with self._lock:
            event = OperationEvent(
                id=self._next_id,
                ts=datetime.now(timezone.utc).isoformat(),
                layer=layer,
                operation=operation,
                status=status,
                payload=payload,
            )
            self._next_id += 1
            self._events.append(event)
            return event

    def list_since(self, last_id: int) -> list[OperationEvent]:
        with self._lock:
            return [event for event in self._events if event.id > last_id]


operation_events = OperationEventStore()


def serialize_events(events: list[OperationEvent]) -> list[dict[str, Any]]:
    return [asdict(event) for event in events]
