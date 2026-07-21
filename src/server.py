from fastapi import FastAPI

from src.api.mcp import router as mcp_router
from src.api.rest import router as rest_router
from src.api.websocket import router as websocket_router

app = FastAPI(
    title="Repo Manager",
    description=(
        "Layered repo manager service with Git operations, REST API, "
        "WebSocket watch feed, and MCP tool interface."
    ),
)

# Layer 2: REST API
app.include_router(rest_router)

# Layer 3: WebSocket watch API
app.include_router(websocket_router)

# Layer 4: MCP interface for AI agents
app.include_router(mcp_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
