# REST API Specification

Source: `src/api/rest.py`

## Endpoints

| Method | Path | Request | Response | Errors |
|--------|------|---------|----------|--------|
| POST | /clone | `{ url, destination?, credential_id?, ssh_identity_id? }` | `{ output, workspace_id? }` | 400 |
| POST | /checkout | `{ workspace_id, branch }` | `{ output }` | 400 |
| POST | /commit | `{ workspace_id, message }` | `{ output }` | 400 |
| POST | /push | `{ workspace_id, remote?, branch? }` | `{ output }` | 400 |
| GET | /file | `?workspace_id=&path=` | `{ content }` | 400, 404 |
| POST | /file | `{ workspace_id, path, content }` | `{ status }` | 400 |
| POST | /exec | `{ workspace_id, cmd }` | `{ output }` | 400 |
| GET | /health | — | `{ status }` | — |

Defaults: `remote='origin'`, `branch='main'`

## Error Contract

Current: FastAPI `detail` strings.  
Target: `{ ok: false, error: { code, message } }`

## Invariants

- Handlers call service-layer only.
- Path handling per [security_baseline.md](../security/security_baseline.md).
- Typed boundaries per [linting/typed_boundaries.md](../linting/typed_boundaries.md).
- Runtime operations are workspace-scoped; callers must provide `workspace_id`.
