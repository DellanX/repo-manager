# Repo Manager Backend

FastAPI backend service with Git operations, REST API, WebSocket watch feed, and MCP tool interface.

## Stack

- Python 3.11+
- FastAPI
- Pydantic for schemas
- SQLite for inventory persistence
- uvicorn for ASGI server

## Development

```bash
# Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install -e .

# Start development server
python -m uvicorn src.server:app --host 0.0.0.0 --port 8888 --reload

# Run tests
pytest

# Lint
ruff check src tests
```

## Project Structure

```
backend/
├── src/
│   ├── api/           # API endpoints (REST, MCP, WebSocket, UI)
│   ├── core/          # Configuration and events
│   ├── models/        # Pydantic schemas
│   └── services/      # Business logic (git, file ops, inventory)
├── tests/             # Unit and integration tests
├── docs/specs/        # Backend-specific specifications
├── pyproject.toml     # Python project configuration
└── requirements.txt   # Python dependencies
```

## API Versioning

All API endpoints use the `/api/v1/` prefix:

- `/api/v1/clone`, `/api/v1/checkout`, etc. - Git operations
- `/api/v1/credentials` - Secure credential metadata lifecycle
- `/api/v1/mcp/*` - MCP tool interface
- `/api/v1/ui/*` - UI data endpoints
- `/api/v1/ws/*` - WebSocket feed
- `/health` - Health check (no version prefix)

See [../docs/specs/api/](../docs/specs/api/) for API specifications.

## Credential Secret Drivers

Credential metadata is stored in SQLite, while secret values use a pluggable driver:

- `REPO_MANAGER_SECRET_DRIVER=keyring` (default)
- `REPO_MANAGER_SECRET_DRIVER=vault-kv-v2`
- `REPO_MANAGER_SECRET_DRIVER=inmemory` (development/testing only)

Vault driver requires:

- `REPO_MANAGER_VAULT_ADDR`
- `REPO_MANAGER_VAULT_TOKEN`

Optional:

- `REPO_MANAGER_VAULT_MOUNT` (default `secret`)
- `REPO_MANAGER_VAULT_PATH_PREFIX` (default `repo-manager/credentials`)
- `REPO_MANAGER_VAULT_NAMESPACE`

Compatibility alias: `REPO_MANAGER_SECRET_BACKEND` is also accepted.

## SSH Identity Files for SSH Clone

The API can generate managed Ed25519 SSH keypairs:

- `POST /api/v1/ssh-identities`
- `GET /api/v1/ssh-identities`
- `DELETE /api/v1/ssh-identities/{identity_id}`

Use `ssh_identity_id` in `POST /api/v1/clone` for SSH clone authentication.
