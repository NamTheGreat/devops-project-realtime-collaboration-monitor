# API Documentation — Real-time Git Collaboration Monitor

## Base URL

```
http://localhost:8000
```

When running via Docker Compose, the frontend Nginx proxy routes `/webhook`, `/ws`, `/events`, and `/stats` to the backend.

---

## REST Endpoints

### `GET /` — Health Check

Returns the service health status.

**Response** `200 OK`
```json
{
  "status": "running",
  "service": "git-collaboration-monitor"
}
```

---

### `POST /webhook` — Receive GitHub Webhook

Receives and processes a GitHub webhook payload. Validates the HMAC-SHA256 signature.

**Request Headers**

| Header | Required | Description |
|--------|----------|-------------|
| `X-Hub-Signature-256` | Yes* | HMAC-SHA256 signature (`sha256=<hex>`) |
| `X-GitHub-Event` | Yes | GitHub event type (`push`, `pull_request`, `create`, `delete`, `issues`) |
| `Content-Type` | Yes | Must be `application/json` |

\* Required when `GITHUB_WEBHOOK_SECRET` is set.

**Request Body**

Standard GitHub webhook payload. See [GitHub Webhook Events documentation](https://docs.github.com/en/webhooks/webhook-events-and-payloads).

**Example** (push event — abbreviated):
```json
{
  "ref": "refs/heads/main",
  "commits": [{ "id": "abc123", "message": "feat: add login", "added": ["src/auth.py"] }],
  "pusher": { "name": "alice" },
  "sender": { "login": "alice", "avatar_url": "https://..." },
  "repository": { "full_name": "octocat/hello-world" }
}
```

**Response** `200 OK`
```json
{
  "status": "received",
  "event_type": "push"
}
```

**Error Responses**

| Status | Description |
|--------|-------------|
| `403 Forbidden` | Invalid HMAC-SHA256 signature |
| `422 Unprocessable Entity` | Malformed JSON payload |

---

### `GET /events/recent` — Recent Events

Returns the last 50 events from the Redis event store.

**Response** `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-02-25T12:00:00+00:00",
    "event_type": "push",
    "actor": "alice",
    "actor_avatar": "https://avatars.githubusercontent.com/u/1?v=4",
    "repository": "octocat/hello-world",
    "branch": "main",
    "title": "alice pushed 3 commits to main",
    "details": { "commits": 3, "compare_url": "https://..." },
    "files_changed": ["src/auth.py", "README.md"],
    "alert": null
  }
]
```

---

### `GET /stats` — Dashboard Statistics

Returns aggregated statistics for the current time windows.

**Response** `200 OK`
```json
{
  "total_events_today": 42,
  "active_contributors": 5,
  "branches_modified": 3,
  "conflict_alerts": 1
}
```

| Field | Description |
|-------|-------------|
| `total_events_today` | Event count since midnight UTC |
| `active_contributors` | Unique actors in the last 1 hour |
| `branches_modified` | Unique branches with activity today |
| `conflict_alerts` | Events with conflict alerts today |

---

## WebSocket Endpoint

### `GET /ws` — Real-time Event Stream

Establishes a persistent WebSocket connection. On connect, the server sends the last 10 events immediately, then streams new events as they arrive.

**Connection URL**
```
ws://localhost:8000/ws
```

**Message Format** (server → client)

Each message is a JSON string representing a `GitEvent`:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-02-25T12:00:00+00:00",
  "event_type": "push",
  "actor": "alice",
  "actor_avatar": "https://avatars.githubusercontent.com/u/1?v=4",
  "repository": "octocat/hello-world",
  "branch": "main",
  "title": "alice pushed 3 commits to main",
  "details": { ... },
  "files_changed": ["src/auth.py"],
  "alert": null
}
```

**Reconnection**: The dashboard automatically reconnects with exponential backoff (3s → 4.5s → 6.75s → ... max 30s).

---

## Authentication — Webhook Signature Verification

GitHub signs webhook payloads using HMAC-SHA256 with the shared secret. The backend verifies this signature:

1. Compute `sha256=` + HMAC-SHA256(secret, request_body)
2. Compare with the `X-Hub-Signature-256` header using constant-time comparison
3. Reject with `403` if signatures don't match

If `GITHUB_WEBHOOK_SECRET` is not set, signature validation is skipped (development mode).

---

## Rate Limiting

Currently no rate limiting is enforced. For production deployments, consider adding:
- Nginx `limit_req` directives for webhook endpoint
- Application-level per-repository rate limiting
- Redis-based sliding window counters
