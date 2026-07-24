# repo-manager

A Repo Management Microservice with a Vue.js frontend and FastAPI backend.

## Monorepo Structure

```
/
├── frontend/          # Vue.js 3 SPA
├── backend/           # FastAPI backend service
├── docs/              # Shared documentation
│   └── specs/api/     # API contracts (shared)
└── Makefile           # Unified dev commands
```

## Quick Start

```bash
# Install all dependencies
make install

# Start development servers (backend on :8888, frontend on :5173)
make dev

# Run all tests
make test

# Lint all code
make lint
```

## Development Commands

| Command             | Description                                 |
| ------------------- | ------------------------------------------- |
| `make dev`          | Start both backend and frontend dev servers |
| `make dev-backend`  | Start only FastAPI backend                  |
| `make dev-frontend` | Start only Vue frontend (with HMR)          |
| `make test`         | Run all tests                               |
| `make lint`         | Lint all code                               |
| `make install`      | Install all dependencies                    |

## Packages

- **[backend/](backend/)** - FastAPI backend with Git operations, REST API, WebSocket, and MCP
- **[frontend/](frontend/)** - Vue.js 3 SPA with TypeScript, Pinia, and Vue Router

## Specifications

Documentation is located in `docs/`:

- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- API specs (shared): [docs/specs/api/](docs/specs/api/)
- Backend specs: [backend/docs/specs/](backend/docs/specs/)
- Frontend specs: [frontend/docs/specs/](frontend/docs/specs/)`
