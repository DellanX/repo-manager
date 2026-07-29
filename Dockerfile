# --------------------------
# Frontend build artifacts
# --------------------------
FROM node:20-bookworm-slim AS frontend-build

WORKDIR /app/frontend

COPY frontend/package*.json /app/frontend/
RUN npm ci --legacy-peer-deps

COPY frontend/ /app/frontend/
RUN npm run build


# --------------------------
# FastAPI runtime base
# --------------------------
FROM python:3.11-slim AS fastapi-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential git \
    && rm -rf /var/lib/apt/lists/*

COPY README.md /app/README.md
COPY backend/requirements.txt /app/backend/requirements.txt
COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY backend/src /app/backend/src

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r /app/backend/requirements.txt \
    && python -m pip install --no-cache-dir -e /app/backend

# --------------------------
# FastAPI image
# --------------------------
FROM fastapi-base AS fastapi

EXPOSE 8888

CMD ["python", "-m", "uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8888"]


# --------------------------
# Frontend production image
# --------------------------
FROM nginx:1.27-alpine AS frontend

COPY --from=frontend-build /app/frontend/dist/ /usr/share/nginx/html/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]


# --------------------------
# Combined production image
# --------------------------
FROM fastapi-base AS combo

# Include built frontend assets for combined deployments.
COPY --from=frontend-build /app/frontend/dist/ /app/frontend-dist/

EXPOSE 8888

CMD ["python", "-m", "uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8888"]


# --------------------------
# Combined devcontainer image
# --------------------------
FROM python:3.11-slim AS combo-dev

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=1000

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        make \
        build-essential \
        gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
        | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" \
        > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid ${USER_GID} ${USERNAME} \
    && useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME}

USER ${USERNAME}

CMD ["sleep", "infinity"]
