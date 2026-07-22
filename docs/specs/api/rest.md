# REST API Specification

Source: `src/api/rest.py`

## Endpoints

| Method | Path | Request | Response | Errors |
|--------|------|---------|----------|--------|
| POST | /clone | `{ url }` | `{ output }` | 400 |
| POST | /checkout | `{ branch }` | `{ output }` | 400 |
| POST | /commit | `{ message }` | `{ output }` | 400 |
| POST | /push | `{ remote?, branch? }` | `{ output }` | 400 |
| GET | /file | `?path=` | `{ content }` | 400, 404 |
| POST | /file | `{ path, content }` | `{ status }` | 400 |
| POST | /exec | `{ cmd }` | `{ output }` | 400 |
| GET | /health | — | `{ status }` | — |

Defaults: `remote='origin'`, `branch='main'`

## Error Contract

Current: FastAPI `detail` strings.  
Target: `{ ok: false, error: { code, message } }`

## Invariants

- Handlers call service-layer only.
- Path handling per [security_baseline.md](../security/security_baseline.md).
- Typed boundaries per [linting/typed_boundaries.md](../linting/typed_boundaries.md).
