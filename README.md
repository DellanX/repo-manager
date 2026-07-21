# repo-manager

A Repo Management Microservice as an API for SW management.

## Development Commands

- Install deps: `python -m pip install --no-cache-dir -r requirements.txt`
- Run API: `python -m uvicorn src.server:app --host 0.0.0.0 --port 8000 --reload`
- Lint: `python -m ruff check src tests`

## Specifications

Specification and architecture docs are located in `docs/`.

- Start here: `docs/README.md`
- Architecture: `docs/ARCHITECTURE.md`
- Module-aligned specs: `docs/specs/`
- Validation and traceability: `docs/implementation/`
