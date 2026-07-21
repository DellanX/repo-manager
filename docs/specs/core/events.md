# Operation Events Specification

Source module: `src/core/events.py`

## Event Model

`OperationEvent`
- `id: int` (monotonic, starts at 1)
- `ts: string` (UTC ISO-8601)
- `layer: string`
- `operation: string`
- `status: string`
- `payload: object`

## Store Behavior

`OperationEventStore`
- `record(layer, operation, status, payload)` appends a new event.
- `list_since(last_id)` returns events with `id > last_id`.
- Thread-safety is protected by a lock.

## Serialization

- `serialize_events(events)` returns list of dictionaries.
- Serialization is direct dataclass field projection.

## Constraints

- Store is in-memory and process-local.
- No retention policy yet; growth is unbounded.

## Future Requirements

- Define retention/TTL.
- Define persistence strategy for durable audit trails.
- Define redaction policy for sensitive payload fields.
