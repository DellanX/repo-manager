from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
