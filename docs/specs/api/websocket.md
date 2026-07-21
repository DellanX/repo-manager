# WebSocket API Specification

Source module: `src/api/websocket.py`

## Endpoint

- `WS /ws/operations`

## Message Types

1. Welcome
- Sent once after connection accept.
- Shape:
  - `type: 'welcome'`
  - `message: string`
  - `note: string`

2. Events batch
- Sent when there are new events in the event store.
- Shape:
  - `type: 'events'`
  - `items: OperationEvent[]`

## Delivery Semantics

- Polling interval is approximately 1 second.
- Event ordering is ascending by event ID.
- Replay scope is current in-memory process lifetime only.
- Disconnect ends stream without server-side session resume.

## Acceptance Criteria

- Welcome frame must always be first message.
- Event payload must match `specs/core/events.md` serialization shape.
- No duplicate event IDs in a single stream session.
