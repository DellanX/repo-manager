#!/bin/bash
set -e

echo "=== Setting up repo-manager devcontainer ==="

# Backend setup
echo ">>> Setting up backend..."
cd /workspace/backend

if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

echo "Installing Python dependencies..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .

# Frontend setup
echo ">>> Setting up frontend..."
cd /workspace/frontend

echo "Installing Node dependencies..."
npm install --legacy-peer-deps

echo "=== Setup complete ==="
echo ""
echo "To start the backend:  cd backend && .venv/bin/uvicorn src.server:app --host 0.0.0.0 --port 8888 --reload"
echo "To start the frontend: cd frontend && npm run dev"
