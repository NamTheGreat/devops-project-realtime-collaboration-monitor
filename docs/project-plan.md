# Project Plan — Real-time Git Collaboration Monitor

## Course: CSE3253 — DevOps | Semester VI (2025-2026)

---

## Phase 1: Architecture Design & Environment Setup (Week 1)

| Task | Status | Deliverable |
|------|--------|-------------|
| Define system architecture and component boundaries | ✅ Complete | `docs/design-document.md` |
| Set up Git repository with branching strategy | ✅ Complete | `.gitignore`, `LICENSE`, `README.md` |
| Configure development environment | ✅ Complete | `.env.example`, `config.yaml` |
| Design data models and API contracts | ✅ Complete | `models.py`, `docs/api-documentation.md` |
| Create project folder structure | ✅ Complete | Full directory tree |

**Milestone**: Architecture design approved, development environment ready.

---

## Phase 2: Backend Development (Week 2)

| Task | Status | Deliverable |
|------|--------|-------------|
| Implement FastAPI webhook endpoint with signature verification | ✅ Complete | `main.py` |
| Build event processor with conflict detection algorithm | ✅ Complete | `processor.py` |
| Implement async Redis client with Pub/Sub | ✅ Complete | `redis_client.py` |
| Build WebSocket connection manager | ✅ Complete | `websocket_manager.py` |
| Write unit tests for processor | ✅ Complete | `tests/unit/test_processor.py` |
| Write unit tests for WebSocket manager | ✅ Complete | `tests/unit/test_websocket_manager.py` |

**Milestone**: Backend API fully functional, all webhook events processed and broadcast.

---

## Phase 3: Frontend Development (Week 3)

| Task | Status | Deliverable |
|------|--------|-------------|
| Set up React + Vite + Tailwind project | ✅ Complete | `package.json`, `vite.config.js` |
| Implement StatsBar component | ✅ Complete | `StatsBar.jsx` |
| Implement LiveFeed component | ✅ Complete | `LiveFeed.jsx` |
| Implement ContributorPanel component | ✅ Complete | `ContributorPanel.jsx` |
| Implement AlertBanner component | ✅ Complete | `AlertBanner.jsx` |
| Implement BranchMap component | ✅ Complete | `BranchMap.jsx` |
| Integrate WebSocket with auto-reconnection | ✅ Complete | `App.jsx` |

**Milestone**: Dashboard fully functional with real-time updates.

---

## Phase 4: Containerization, CI/CD & Monitoring (Week 4)

| Task | Status | Deliverable |
|------|--------|-------------|
| Write Dockerfiles for backend and frontend | ✅ Complete | `Dockerfile.backend`, `Dockerfile.frontend` |
| Configure Nginx reverse proxy | ✅ Complete | `nginx.conf` |
| Create Docker Compose for full stack | ✅ Complete | `docker-compose.yml` |
| Write Kubernetes manifests | ✅ Complete | `deployment.yaml`, `service.yaml`, `configmap.yaml` |
| Build GitHub Actions CI/CD pipeline | ✅ Complete | `ci-cd.yml` |
| Build Jenkins pipeline | ✅ Complete | `Jenkinsfile` |
| Configure Nagios monitoring | ✅ Complete | `nagios.cfg` |
| Define alert rules | ✅ Complete | `alert_rules.yaml` |

**Milestone**: One-command deployment with `docker-compose up --build`.

---

## Phase 5: Testing, Documentation & Demo (Week 5)

| Task | Status | Deliverable |
|------|--------|-------------|
| Write integration tests | ✅ Complete | `test_webhook_endpoint.py` |
| Create event simulation script | ✅ Complete | `simulate_events.py` |
| Write design document | ✅ Complete | `design-document.md` |
| Write API documentation | ✅ Complete | `api-documentation.md` |
| Write user guide | ✅ Complete | `user-guide.md` |
| Complete project plan | ✅ Complete | `project-plan.md` |
| Prepare demo script | ✅ Complete | `demo-script.md` |
| Complete self-assessment | ✅ Complete | `self-assessment.md` |
| Finalize README | ✅ Complete | `README.md` |

**Milestone**: All documentation complete, project ready for submission and demo.

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| GitHub webhook delivery failures | Simulation script for offline testing |
| Redis downtime | Retry logic with 3 attempts, graceful degradation |
| WebSocket connection drops | Exponential backoff reconnection (3s–30s) |
| Container build failures | Multi-stage builds, CI/CD pipeline validates builds |
