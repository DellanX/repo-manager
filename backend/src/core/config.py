import os

WORKSPACE = os.getenv("REPO_MANAGER_WORKSPACE", os.getcwd())

# Ensure workspace exists at startup (skip if it already exists or if we're in a read-only context).
if not os.path.isdir(WORKSPACE):
    os.makedirs(WORKSPACE, exist_ok=True)
