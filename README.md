# Real-time Git Collaboration Monitor

> **Course**: CSE3253 — DevOps | **Semester**: VI (2025-2026)
>
> **Student**: Naman Kalia

A production-grade, fully containerized DevOps tool that listens to GitHub webhook events and displays live repository activity on a real-time dashboard. Features conflict detection, contributor analytics, and branch mapping.

---

## Problem Statement

In collaborative software development, teams working on the same repository often lack real-time visibility into concurrent changes across branches. This leads to unexpected merge conflicts, duplicated effort, and delayed integration. There is a need for a centralized, real-time monitoring tool that surfaces concurrent activity and proactively alerts teams to potential conflicts.

## Objectives

1. Build a real-time event processing pipeline that ingests GitHub webhooks and broadcasts normalized events via WebSocket
2. Implement a conflict detection algorithm that identifies overlapping file modifications across branches
3. Create a containerized, production-ready deployment with CI/CD, monitoring, and Kubernetes support

## Key Features

1. **Real-time Event Streaming** — GitHub webhooks → Redis Pub/Sub → WebSocket → Dashboard (no polling)
2. **Conflict Detection** — Proactive alerts when multiple branches modify the same files within 10 minutes
3. **Live Dashboard** — Dark terminal-aesthetic React UI with animated stats, event feed, contributor sparklines, and branch map
4. **Single-Command Deployment** — `docker-compose up --build` starts all 4 services
5. **Event Simulation** — Built-in simulator for testing without a real GitHub repository

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | Python 3.11, FastAPI, Uvicorn | Webhook handler, REST API, WebSocket server |
| Message Broker | Redis 7 (Pub/Sub + Lists) | Real-time event broadcasting and short-term storage |
| Frontend | React 18, Vite 5, Tailwind CSS 3 | Dashboard with live WebSocket updates |
| Reverse Proxy | Nginx | Static file serving, API/WebSocket proxying |
| Containerization | Docker, Docker Compose | Multi-service deployment |
| Orchestration | Kubernetes | Production scaling manifests |
| CI/CD | GitHub Actions, Jenkins | Automated lint, test, build, scan, deploy |
| Monitoring | Nagios | Service health monitoring and alerting |
| Testing | pytest, httpx | Unit and integration tests |

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 4.x+
- [Git](https://git-scm.com/) 2.x+
- Python 3.11+ (for running the simulation script locally)

---

## Installation & Running

### Docker Method (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/devops-project-realtime-collaboration-monitor.git
cd devops-project-realtime-collaboration-monitor

# 2. Configure environment
cp .env.example .env
# Edit .env with your webhook secret

# 3. Start all services
cd infrastructure/docker
docker-compose up --build

# 4. Open the dashboard
# → http://localhost:3000
```

### Manual Method (Development)

```bash
# Backend
cd src/main/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd src/main/frontend
npm install
npm run dev

# Redis (separate terminal or Docker)
docker run -d -p 6379:6379 redis:7-alpine
```

### Simulation (Testing Without GitHub)

```bash
pip install requests
python src/scripts/simulate_events.py
```

---

## Project Structure

```
devops-project-realtime-collaboration-monitor/
├── README.md
├── .gitignore
├── LICENSE
├── .env.example
├── src/
│   ├── main/
│   │   ├── backend/
│   │   │   ├── main.py              # FastAPI application
│   │   │   ├── processor.py         # Event parsing & conflict detection
│   │   │   ├── redis_client.py      # Async Redis client
│   │   │   ├── websocket_manager.py # WebSocket connection manager
│   │   │   ├── models.py            # Pydantic data models
│   │   │   ├── requirements.txt
│   │   │   └── config/config.yaml
│   │   └── frontend/
│   │       ├── package.json
│   │       ├── vite.config.js
│   │       ├── tailwind.config.js
│   │       ├── index.html
│   │       └── src/
│   │           ├── App.jsx
│   │           ├── main.jsx
│   │           ├── index.css
│   │           └── components/
│   │               ├── LiveFeed.jsx
│   │               ├── ContributorPanel.jsx
│   │               ├── AlertBanner.jsx
│   │               ├── StatsBar.jsx
│   │               └── BranchMap.jsx
│   └── scripts/
│       ├── setup_webhook.sh
│       └── simulate_events.py
├── docs/
│   ├── project-plan.md
│   ├── design-document.md
│   ├── user-guide.md
│   └── api-documentation.md
├── infrastructure/
│   ├── docker/
│   │   ├── Dockerfile.backend
│   │   ├── Dockerfile.frontend
│   │   ├── nginx.conf
│   │   └── docker-compose.yml
│   └── kubernetes/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── configmap.yaml
├── pipelines/
│   ├── Jenkinsfile
│   └── .github/workflows/ci-cd.yml
├── tests/
│   ├── unit/
│   │   ├── test_processor.py
│   │   └── test_websocket_manager.py
│   ├── integration/
│   │   └── test_webhook_endpoint.py
│   └── test-data/
│       ├── sample_push_event.json
│       ├── sample_pr_event.json
│       └── sample_branch_event.json
├── monitoring/
│   ├── nagios/nagios.cfg
│   └── alerts/alert_rules.yaml
├── presentations/demo-script.md
└── deliverables/assessment/self-assessment.md
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_WEBHOOK_SECRET` | — | HMAC-SHA256 signing secret for webhook validation |
| `REDIS_HOST` | `redis` | Redis server hostname |
| `REDIS_PORT` | `6379` | Redis server port |
| `APP_ENV` | `development` | Application environment |
| `WEBHOOK_URL` | `http://localhost:8000/webhook` | Webhook URL (for simulation script) |

---

## CI/CD Pipeline Stages

| Stage | Description | Trigger |
|-------|-------------|---------|
| Lint & Format Check | flake8 (Python), ESLint (JS) | All pushes and PRs |
| Unit Tests | pytest with coverage | After lint passes |
| Integration Tests | pytest with Redis service | After unit tests |
| Build Docker Images | Backend + Frontend images, tagged with SHA | After integration tests |
| Security Scan | Trivy vulnerability scan (fail on CRITICAL) | After build |
| Deploy Staging | Docker Compose deployment | Push to `develop` |
| Deploy Production | Docker Compose with manual approval | Push to `main` |

---

## Testing

```bash
# Unit tests
PYTHONPATH=src/main/backend pytest tests/unit/ -v

# Integration tests (requires Redis)
PYTHONPATH=src/main/backend pytest tests/integration/ -v

# All tests
PYTHONPATH=src/main/backend pytest tests/ -v
```

---

## Monitoring

| Service | URL | What It Monitors |
|---------|-----|-----------------|
| Nagios | http://localhost:8081 | Backend health, Redis connectivity, Frontend availability |

Alert rules defined in `monitoring/alerts/alert_rules.yaml` cover:
- Backend HTTP health (status ≠ 200 → critical)
- Redis TCP connectivity (connection failure → critical)
- High conflict rate (>10/hour → warning)

---

## Docker Commands

```bash
# Start all services
cd infrastructure/docker && docker-compose up --build

# Start in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down

# Remove volumes
docker-compose down -v
```

## Kubernetes Commands

```bash
# Apply all manifests
kubectl apply -f infrastructure/kubernetes/

# Check deployments
kubectl get deployments

# Check services
kubectl get services

# View backend logs
kubectl logs -l app=git-monitor,component=backend
```

---

## Performance Metrics

| Metric | Target | Notes |
|--------|--------|-------|
| Webhook processing latency | < 100ms | Parse + conflict check + Redis publish |
| WebSocket broadcast latency | < 50ms | Redis Pub/Sub to client delivery |
| Dashboard initial load | < 2s | Vite production build + Nginx gzip |
| Concurrent WebSocket connections | 100+ | Tested with WebSocket manager |
| Event throughput | 50+ events/sec | Limited by Redis single-instance performance |

---

## Documentation

- [Design Document](docs/design-document.md) — Architecture, data models, algorithms
- [API Documentation](docs/api-documentation.md) — REST + WebSocket endpoint reference
- [User Guide](docs/user-guide.md) — Setup, configuration, and troubleshooting
- [Project Plan](docs/project-plan.md) — 5-phase development timeline

---

## Git Branching Strategy

```
main ─────────────────────────────────────────────
  │                                    ↑
  └── develop ─────────────────────────┤
        │          ↑         ↑         │
        ├── feature/auth ────┘         │
        ├── feature/dashboard ─────────┘
        └── hotfix/bug-42 ─────────────→ main
```

- `main` — Production-ready code
- `develop` — Integration branch for features
- `feature/*` — Feature development branches
- `hotfix/*` — Critical bug fixes (merge to both `main` and `develop`)

---

## Commit Convention

All commits follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

| Prefix | Description |
|--------|-------------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation changes |
| `refactor:` | Code restructuring |
| `test:` | Test additions/changes |
| `chore:` | Maintenance tasks |
| `ci:` | CI/CD pipeline changes |

---

## Security Measures

- [x] HMAC-SHA256 webhook signature verification
- [x] No hardcoded secrets — all via environment variables
- [x] Docker image vulnerability scanning (Trivy) in CI/CD
- [x] Network isolation via Docker bridge network
- [x] Nginx reverse proxy for frontend (no direct backend exposure)
- [x] CORS configuration (restrict in production)
- [x] Redis on private network (not exposed in Kubernetes)

---

## Self-Assessment

See [deliverables/assessment/self-assessment.md](deliverables/assessment/self-assessment.md) for the full assessment rubric.

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
