# REST API Specification

Source module: `src/api/rest.py`

## Endpoints

1. `POST /clone`
- Request: `CloneRequest { url }`
- Response: `{ output: string }`
- Errors: 400 on operation failure.

2. `POST /checkout`
- Request: `CheckoutRequest { branch }`
- Response: `{ output: string }`
- Errors: 400 on operation failure.

3. `POST /commit`
- Request: `CommitRequest { message }`
- Response: `{ output: string }`
- Errors: 400 on operation failure.

4. `POST /push`
- Request: `PushRequest { remote='origin', branch='main' }`
- Response: `{ output: string }`
- Errors: 400 on operation failure.

5. `GET /file?path=<relative-path>`
- Response: `{ content: string }`
- Errors: 404 when file missing, 400 for invalid path or operation failure.

6. `POST /file`
- Request: `WriteFileRequest { path, content }`
- Response: `{ status: 'ok' }`
- Errors: 400 on invalid path or write failure.

7. `POST /exec`
- Request: `ExecRequest { cmd }`
- Response: `{ output: string }`
- Errors: 400 on command failure or policy rejection.

8. `GET /health`
- Response: `{ status: 'ok' }`

## Error Contract

Current implementation returns FastAPI `detail` strings. The target contract should converge on:

- `{ ok: false, error: { code, message, details? } }`

Until migration, tests must verify current behavior and track migration as a compatibility change.

## Acceptance Criteria

- Route handlers must call only service-layer functions.
- `OperationError` must map to deterministic 4xx status codes.
- File path handling must comply with security baseline.
