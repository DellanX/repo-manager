# Repo Manager Frontend

Vue.js 3 SPA for the Repo Manager dashboard.

## Stack

- Vue 3 + TypeScript
- Vue Router for navigation
- Pinia for state management
- Vite for development and build
- Vitest for unit testing

## Development

```bash
# Install dependencies
npm install

# Start dev server with HMR (proxies API to backend)
npm run dev

# Run unit tests
npm run test:unit

# Lint and format
npm run lint
npm run format

# Build for production
npm run build
```

## Project Structure

```
frontend/
├── src/
│   ├── api/           # API client for backend communication
│   ├── assets/        # CSS and static assets
│   ├── components/    # Reusable Vue components
│   ├── router/        # Vue Router configuration
│   ├── stores/        # Pinia stores
│   └── views/         # Page components
├── docs/specs/        # UI/UX specifications
├── public/            # Static files
└── tests/             # Unit tests
```

## API Integration

The frontend communicates with the backend via `/api/v1/*` endpoints. In development,
Vite proxies these requests to `http://localhost:8000` (the FastAPI backend).

See [docs/specs/webui.md](docs/specs/webui.md) and [docs/specs/ux.md](docs/specs/ux.md)
for UI specifications.
