# AI Context — Real-time Git Collaboration Monitor

This document provides essential context for AI agents working on this project.

## 1. Project Overview
A DevOps tool for real-time monitoring of GitHub activity. It receives webhooks, processes them (including conflict detection), and streams updates via WebSocket to a live dashboard.

## 2. Architecture & Data Flow
- **GitHub → Backend**: POST `/webhook` (HMAC-SHA256 validated).
- **Backend → Redis**: Normalized event published to `git-events` channel (Pub/Sub) and appended to `recent-events` list.
- **Redis → WebSocket**: `WebSocketManager` listens to Redis and broadcasts to all dashboard clients.
- **Backend → Frontend**: Initial state hydrated via `/events/recent` and `/stats`.

## 3. Tech Stack
- **Backend**: Python 3.11, FastAPI, `redis-py` (async), `pydantic`.
- **Frontend**: React 18, Vite, Tailwind CSS (Terminal/Industrial aesthetic).
- **Infrastructure**: Docker, Docker Compose, Nginx, Kubernetes, Nagios.
- **CI/CD**: GitHub Actions, Jenkins.

## 4. Key Directories
- `src/main/backend/`: FastAPI app, processor logic, redis/ws managers.
- `src/main/frontend/src/`: React source code (components, App, hooks).
- `infrastructure/docker/`: Dockerfiles and Compose setup.
- `infrastructure/kubernetes/`: K8s manifests.
- `tests/`: Unit and integration test suites.
- `docs/`: Technical and user documentation.

## 5. Conflict Detection Logic (`processor.py`)
Checks if a `push` event modifies files that were modified by a **different** branch within the last 10 minutes (configurable window). Uses the last 20 events from Redis for comparison.

## 6. Coding Standards
- **Python**: PEP8 compliant, async/await for I/O, Pydantic for validation.
- **JS/React**: Functional components, Hooks, tailwind utility classes for all styling.
- **Naming**: Conventional commits for Git, snake_case for Python, PascalCase for React components.

## 7. Development Commands
```bash
# Start all services
cd infrastructure/docker && docker-compose up --build

# Run tests
PYTHONPATH=src/main/backend pytest tests/

# Simulate events
python src/scripts/simulate_events.py
```

## 8. Critical Files to Refer To
- `src/main/backend/models.py`: Data schemas.
- `infrastructure/docker/nginx.conf`: Routing/Proxy logic.
- `pipelines/.github/workflows/ci-cd.yml`: Pipeline logic.
- `README.md`: Overall project guide.
