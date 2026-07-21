import os

WORKSPACE = os.getenv("REPO_MANAGER_WORKSPACE", "/workspace")

# Ensure workspace exists at startup.
os.makedirs(WORKSPACE, exist_ok=True)
