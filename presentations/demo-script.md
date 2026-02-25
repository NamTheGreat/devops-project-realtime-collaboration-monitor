# Demo Script — Real-time Git Collaboration Monitor

## Pre-Demo Checklist

- [ ] Docker Desktop running
- [ ] Terminal ready for commands
- [ ] Browser open (Chrome/Firefox recommended)
- [ ] `.env` file configured with a webhook secret

---

## Demo Flow (10 minutes)

### 1. Introduction (1 minute)

> "This is the Real-time Git Collaboration Monitor — a DevOps tool that listens to GitHub webhook events and displays live repository activity on a dashboard. It uses FastAPI, Redis Pub/Sub, WebSocket, and React. Let me show you how it works."

### 2. Start the Stack (1 minute)

```bash
cd infrastructure/docker
docker-compose up --build
```

> "With a single command, Docker Compose starts four services: the FastAPI backend, the React frontend served by Nginx, Redis for real-time messaging, and Nagios for monitoring."

Wait for all services to be healthy. Point out the Redis healthcheck log.

### 3. Open the Dashboard (1 minute)

Open **http://localhost:3000** in the browser.

> "The dashboard connects via WebSocket — you can see the green 'CONNECTED' indicator. Right now it shows 'Waiting for events…' because no webhooks have been sent yet."

Point out: StatsBar, LiveFeed, ContributorPanel, BranchMap sections.

### 4. Run the Simulator (3 minutes)

In a new terminal:
```bash
python src/scripts/simulate_events.py
```

> "The simulator generates realistic GitHub webhook events — pushes, pull requests, branch creations, and issues. Watch the dashboard update in real time without any page refresh."

Demonstrate:
- Events appearing with slide-in animation
- Stats counters incrementing
- Contributor list populating with sparklines
- Branch tags appearing in the panel

### 5. Conflict Detection (2 minutes)

> "Every 10th event, the simulator deliberately creates a conflict scenario — two branches modifying the same file. Watch for the alert banner."

When a conflict appears:
- Point out the amber/red alert banner
- Show the conflicting branches and files
- Show the dashed red line in the BranchMap connecting those branches
- Demonstrate dismissing the alert manually

### 6. API & Architecture (1 minute)

Open a new terminal:
```bash
# Health check
curl http://localhost:8000/

# Recent events
curl http://localhost:8000/events/recent | python -m json.tool | head -30

# Stats
curl http://localhost:8000/stats
```

> "The backend also exposes REST endpoints. The `/stats` endpoint aggregates metrics — events today, active contributors, branches modified, and conflict counts."

### 7. Wrap-up (1 minute)

> "To summarize: this project demonstrates real-time event processing with webhook signature verification, Redis Pub/Sub for message brokering, WebSocket for live dashboard updates, containerized deployment with Docker Compose, CI/CD with GitHub Actions and Jenkins, monitoring with Nagios, and Kubernetes manifests for production scaling."

Stop the services:
```bash
docker-compose down
```

---

## Key Talking Points

- **Real-time**: No polling — events push from GitHub → Redis Pub/Sub → WebSocket → Dashboard
- **Security**: HMAC-SHA256 webhook verification, no hardcoded secrets
- **DevOps practices**: Docker, Docker Compose, Kubernetes, CI/CD, Nagios monitoring
- **Conflict detection**: Proactive alert when branches modify the same files
- **Resilient**: Retry logic, WebSocket reconnection, graceful degradation
