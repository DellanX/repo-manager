import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from src.api.mcp import router as mcp_router
from src.api.rest import router as rest_router
from src.api.ui import router as ui_router
from src.api.websocket import router as websocket_router

app = FastAPI(
    title="Repo Manager",
    description=(
        "Layered repo manager service with Git operations, REST API, "
        "WebSocket watch feed, MCP tool interface, and Web UI inventory."
    ),
)

# CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Layer 2: REST API
app.include_router(rest_router, prefix="/api/v1")

# Layer 3: WebSocket watch API
app.include_router(websocket_router, prefix="/api/v1")

# Layer 4: MCP interface for AI agents
app.include_router(mcp_router, prefix="/api/v1")

# Layer 5: Web UI API
app.include_router(ui_router, prefix="/api/v1")


def _frontend_dist_paths() -> tuple[Path, Path]:
    frontend_dist = Path(os.getenv("FRONTEND_DIST_DIR", "/app/frontend-dist")).resolve()
    return frontend_dist, frontend_dist / "index.html"


def _frontend_file(frontend_dist: Path, requested_path: str) -> Path | None:
    candidate = (frontend_dist / requested_path).resolve()
    try:
        candidate.relative_to(frontend_dist)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


FRONTEND_DIST, FRONTEND_INDEX = _frontend_dist_paths()
SERVE_FRONTEND = FRONTEND_INDEX.is_file()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if SERVE_FRONTEND:

    @app.get("/", include_in_schema=False)
    def frontend_root() -> FileResponse:
        return FileResponse(FRONTEND_INDEX)

    @app.get("/{path:path}", include_in_schema=False)
    def frontend_spa(path: str) -> FileResponse:
        # Keep backend routes and docs returning backend 404s instead of SPA index.
        if path.startswith(("api/", "docs", "redoc", "openapi.json", "health")):
            raise HTTPException(status_code=404, detail="Not Found")

        candidate = _frontend_file(FRONTEND_DIST, path)
        if candidate is not None:
            return FileResponse(candidate)

        return FileResponse(FRONTEND_INDEX)
