# Operation Events Specification

Source: `src/core/events.py`

## Event Model

```
OperationEvent { id, ts, layer, operation, status, payload }
```

- `id`: monotonic int (starts 1)
- `ts`: UTC ISO-8601

## Store API

| Method | Behavior |
|--------|----------|
| `record(layer, op, status, payload)` | Append event |
| `list_since(last_id)` | Events where id > last_id |

Thread-safe (lock-protected).

## Constraints

- In-memory, process-local.
- No retention policy yet (unbounded growth).

## Future

- Retention/TTL
- Persistence for audit
- Redaction for sensitive payloads
