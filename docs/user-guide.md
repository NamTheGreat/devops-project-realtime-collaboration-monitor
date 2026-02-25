# User Guide — Real-time Git Collaboration Monitor

## 1. Prerequisites

Before starting, ensure you have the following installed:

| Tool | Version | Purpose |
|------|---------|---------|
| Docker Desktop | 4.x+ | Container runtime |
| Docker Compose | 2.x+ | Multi-container orchestration |
| Git | 2.x+ | Version control |
| Python 3.11+ | 3.11+ | Running simulation script locally |
| GitHub Account | — | Webhook configuration (optional) |

## 2. Cloning and Setup

```bash
# Clone the repository
git clone https://github.com/<your-username>/devops-project-realtime-collaboration-monitor.git
cd devops-project-realtime-collaboration-monitor

# Copy environment variables
cp .env.example .env

# Edit .env with your webhook secret
# GITHUB_WEBHOOK_SECRET=choose_a_strong_random_secret
```

## 3. Setting Up a GitHub Webhook

To receive real events from a GitHub repository:

1. Go to your repository on GitHub → **Settings** → **Webhooks** → **Add webhook**
2. **Payload URL**: Enter your server's public URL + `/webhook` (e.g., `https://your-server.com/webhook`)
3. **Content type**: Select `application/json`
4. **Secret**: Enter the same value as `GITHUB_WEBHOOK_SECRET` in your `.env` file
5. **Events**: Select "Let me select individual events" and check:
   - ✅ Pushes
   - ✅ Pull requests
   - ✅ Branch or tag creation
   - ✅ Branch or tag deletion
   - ✅ Issues
6. Click **Add webhook**

> **Note**: For local development, use a tunnel tool like [ngrok](https://ngrok.com) to expose your local port: `ngrok http 8000`

Alternatively, use the provided setup script:
```bash
export GITHUB_TOKEN=your_personal_access_token
bash src/scripts/setup_webhook.sh owner/repo https://your-server.com/webhook your-secret
```

## 4. Running with Docker Compose

```bash
cd infrastructure/docker
docker-compose up --build
```

This starts four services:

| Service | Port | Description |
|---------|------|-------------|
| Backend | 8000 | FastAPI API + WebSocket server |
| Frontend | 3000 | React dashboard (Nginx) |
| Redis | 6379 | Message broker + event store |
| Nagios | 8081 | Infrastructure monitoring |

Open the dashboard at **http://localhost:3000**.

To stop all services:
```bash
docker-compose down
```

## 5. Using the Simulation Script

For testing without a real GitHub repository, the simulation script generates realistic webhook events:

```bash
# Install requests if not in a venv
pip install requests

# Run the simulator (from project root)
python src/scripts/simulate_events.py
```

The simulator will:
- Send random push, PR, branch, and issue events every 2-5 seconds
- Create deliberate conflict scenarios every 10th event
- Print coloured output showing what was sent

Environment variables:
- `WEBHOOK_URL` — Target URL (default: `http://localhost:8000/webhook`)
- `WEBHOOK_SECRET` — Must match `GITHUB_WEBHOOK_SECRET` in `.env`

## 6. Reading the Dashboard

### Stats Bar (Top)
Four key metrics updated every 30 seconds:
- **Events Today**: Total webhook events since midnight
- **Active Contributors**: Unique committers in the last hour
- **Branches Modified**: Branches with activity today
- **Conflict Alerts**: Number of conflict warnings

A pulsing **green dot** indicates a live WebSocket connection; **red** means it's reconnecting.

### Live Feed (Left, 60%)
A scrollable, chronological feed of all events:
- 🟢 Green dot = push event
- 🔵 Blue dot = pull request / merge
- 🟡 Yellow dot = branch create / delete
- 🔴 Red border = event with a conflict alert
- Click **"Show N file(s)"** to expand the changed file list

### Contributor Panel (Right, 40%)
- Ranked list of active contributors with event counts and sparklines
- **Branch Activity** section: click a branch tag to filter the feed

### Alert Banner
Appears below the stats bar when conflicts are detected. Shows which branches and files are in conflict. Alerts auto-dismiss after 60 seconds or can be manually closed.

### Branch Map (Bottom right)
SVG visualization of active branches. Dashed red lines connect branches that recently modified the same files (conflict risk).

## 7. Troubleshooting

### Redis not connecting
```
Error: Cannot connect to Redis at redis:6379
```
- Ensure the Redis container is running: `docker-compose ps`
- Check Redis logs: `docker-compose logs redis`
- Verify `REDIS_HOST` and `REDIS_PORT` in `.env`

### Webhook not receiving events
- Verify the webhook URL is reachable from GitHub (use ngrok for local dev)
- Check the webhook delivery log in GitHub → Settings → Webhooks → Recent Deliveries
- Ensure the secret matches between GitHub and `.env`
- Check backend logs: `docker-compose logs backend`

### WebSocket disconnecting
- The dashboard auto-reconnects with exponential backoff (up to 30s delay)
- If persistently disconnecting, check backend logs for errors
- Ensure the Nginx WebSocket proxy is configured correctly (check `nginx.conf`)

### Dashboard shows "Waiting for events…"
- Run the simulation script to generate test events
- Verify the backend is running: `curl http://localhost:8000/`
- Check that Redis is healthy: `docker-compose exec redis redis-cli ping`
