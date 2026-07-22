# WebSocket API Specification

Source: `src/api/websocket.py`

## Endpoint

`WS /ws/operations`

## Messages

| Type | Shape | When |
|------|-------|------|
| welcome | `{ type, message, note }` | On connect |
| events | `{ type, items: Event[] }` | Polling (~1s) |

## Delivery

- Ascending event ID order.
- In-memory replay only (process lifetime).
- No session resume on disconnect.

## Invariants

- Welcome must be first message.
- Event shape per [events.md](../core/events.md).
- No duplicate IDs per session.
