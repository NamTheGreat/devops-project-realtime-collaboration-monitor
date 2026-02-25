# Design Document — Real-time Git Collaboration Monitor

## 1. System Architecture Overview

The Real-time Git Collaboration Monitor is a full-stack DevOps tool composed of five primary subsystems that work together to provide live visibility into GitHub repository activity.

```
┌──────────────┐     ┌────────────────────────────────────────────────┐
│   GitHub      │     │              Docker Compose Network             │
│   Webhooks    │────▶│  ┌──────────┐  ┌─────────┐  ┌──────────────┐ │
│              │     │  │ FastAPI  │──│  Redis  │──│  WebSocket   │ │
└──────────────┘     │  │ Backend  │  │ Pub/Sub │  │  Manager     │ │
                      │  └────┬─────┘  └─────────┘  └──────┬───────┘ │
                      │       │                            │         │
                      │  ┌────┴─────┐              ┌──────┴───────┐ │
                      │  │ Event    │              │  React       │ │
                      │  │ Processor│              │  Dashboard   │ │
                      │  └──────────┘              └──────────────┘ │
                      │                                              │
                      │  ┌──────────┐                                │
                      │  │ Nagios   │  (monitoring)                  │
                      │  └──────────┘                                │
                      └────────────────────────────────────────────────┘
```

## 2. Component Descriptions

### 2.1 Webhook Handler (`main.py`)
The FastAPI application serves as the entry point for all GitHub webhook events. It validates incoming payloads using HMAC-SHA256 signature verification against a shared secret, ensuring only legitimate GitHub events are processed. The handler extracts the event type from the `X-GitHub-Event` header and delegates to the Event Processor.

### 2.2 Event Processor (`processor.py`)
The core logic module that normalizes raw GitHub webhook payloads into a consistent `GitEvent` schema. It handles five event types (push, pull_request, create, delete, issues) and generates human-readable titles. The conflict detection algorithm compares file paths modified by different branches within a 10-minute sliding window to identify merge conflict risks.

### 2.3 Redis Pub/Sub (`redis_client.py`)
Redis serves dual purposes: (1) as a Pub/Sub message broker — events are published to the `git-events` channel for real-time broadcasting, and (2) as a short-term data store — the `recent-events` list maintains the last 100 events for new client hydration and statistics computation.

### 2.4 WebSocket Manager (`websocket_manager.py`)
Maintains a set of active WebSocket connections to dashboard clients. On client connect, it sends the last 10 events immediately so dashboards aren't blank. A background task subscribes to the Redis Pub/Sub channel and broadcasts every incoming message to all connected clients. Dead connections are silently pruned during broadcast.

### 2.5 React Dashboard (Frontend)
A dark-themed, terminal-aesthetic React application built with Vite and Tailwind CSS. It features:
- **StatsBar**: Four animated metric counters with connection status
- **LiveFeed**: Scrollable event feed with colour-coded dots and collapsible file lists
- **ContributorPanel**: Ranked contributor list with CSS sparklines and branch filtering
- **AlertBanner**: Severity-coloured conflict alerts with auto-dismiss
- **BranchMap**: SVG visualization of active branches and conflict connections

## 3. Data Flow Walkthrough

1. **Developer pushes code** to a GitHub repository
2. **GitHub fires a webhook** POST request to the configured URL
3. **FastAPI receives the request** and validates the HMAC-SHA256 signature
4. **Event Processor normalizes** the raw payload into a `GitEvent` object
5. **Conflict Detector checks** the last 20 push events for overlapping file modifications
6. **Redis publishes** the normalized event to the `git-events` channel and stores it in the `recent-events` list
7. **WebSocket Manager receives** the published message via its Redis subscriber
8. **Dashboard clients receive** the event via WebSocket and render it in real time

## 4. Data Models

### GitEvent Schema
```json
{
  "id": "uuid4",
  "timestamp": "ISO 8601",
  "event_type": "push | pull_request | branch_create | branch_delete | merge | issues",
  "actor": "GitHub username",
  "actor_avatar": "URL",
  "repository": "owner/repo",
  "branch": "branch name",
  "title": "human-readable summary",
  "details": { "event-specific fields" },
  "files_changed": ["file paths"],
  "alert": null | ConflictAlert
}
```

### ConflictAlert Schema
```json
{
  "type": "conflict_risk",
  "severity": "high | medium",
  "message": "Human-readable conflict description",
  "branches": ["branch1", "branch2"],
  "conflicting_files": ["file paths"]
}
```

## 5. Conflict Detection Algorithm

The algorithm works as follows:
1. On every incoming push event, retrieve the last 20 push events from Redis
2. Filter events to only those within the last 10 minutes
3. For each recent push from a **different** branch, compute the intersection of modified files
4. If any intersection exists, generate a conflict alert with severity based on count:
   - **High**: 3 or more conflicting files
   - **Medium**: 1-2 conflicting files
5. Attach the alert to the event before publishing

## 6. Scalability Considerations

For monitoring 100+ repositories, the following changes would be needed:
- **Redis Cluster**: Replace single Redis instance with a cluster for horizontal scaling
- **Backend Replicas**: Run multiple FastAPI instances behind a load balancer (already supported by the Kubernetes deployment with 2 replicas)
- **Event Partitioning**: Partition events by repository into separate Redis channels to reduce per-subscriber message volume
- **Database Backend**: Add PostgreSQL for long-term event storage beyond the 100-event Redis window
- **Rate Limiting**: Implement per-repository rate limiting to prevent webhook storms

## 7. Security Considerations

- **Webhook Secret Validation**: All incoming webhook payloads are verified using HMAC-SHA256, preventing forged events
- **CORS Configuration**: Currently allows all origins for development — should be restricted to specific domains in production
- **No Hardcoded Secrets**: All secrets are loaded from environment variables
- **Container Security**: Docker images are scanned with Trivy in the CI/CD pipeline, failing on CRITICAL vulnerabilities
- **Network Isolation**: Docker Compose services communicate on a private bridge network
