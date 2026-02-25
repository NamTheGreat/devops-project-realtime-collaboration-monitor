#!/usr/bin/env python3
"""
simulate_events.py — Webhook event simulator for the Git Collaboration Monitor.

Generates and sends realistic GitHub-style webhook events to the local backend
for development and testing. Deliberately creates conflict scenarios every 10th event.

Usage:
    python simulate_events.py

Environment Variables:
    WEBHOOK_SECRET  — HMAC-SHA256 signing secret (default: empty)
    WEBHOOK_URL     — Backend webhook URL (default: http://localhost:8000/webhook)
"""

import hashlib
import hmac
import json
import os
import random
import sys
import time
import uuid
from datetime import datetime, timezone

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", os.getenv("GITHUB_WEBHOOK_SECRET", ""))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://localhost:8000/webhook")

CONTRIBUTORS = [
    {"login": "alice", "avatar_url": "https://avatars.githubusercontent.com/u/1?v=4"},
    {"login": "bob", "avatar_url": "https://avatars.githubusercontent.com/u/2?v=4"},
    {"login": "carol", "avatar_url": "https://avatars.githubusercontent.com/u/3?v=4"},
    {"login": "dave", "avatar_url": "https://avatars.githubusercontent.com/u/4?v=4"},
    {"login": "eve", "avatar_url": "https://avatars.githubusercontent.com/u/5?v=4"},
]

BRANCHES = ["main", "feature/auth", "feature/dashboard", "hotfix/bug-42"]

FILES = [
    "src/auth.py",
    "src/main.py",
    "src/utils.py",
    "src/database.py",
    "src/api/routes.py",
    "src/api/middleware.py",
    "tests/test_auth.py",
    "config/settings.yaml",
    "README.md",
    "docs/api.md",
]

PR_COUNTER = 40
EVENT_COUNTER = 0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sign_payload(payload_bytes: bytes) -> str:
    """Generate HMAC-SHA256 signature for the payload."""
    if not WEBHOOK_SECRET:
        return ""
    return "sha256=" + hmac.new(WEBHOOK_SECRET.encode(), payload_bytes, hashlib.sha256).hexdigest()


def send_event(event_type: str, payload: dict) -> bool:
    """Sign and POST a webhook payload. Returns True on success."""
    body = json.dumps(payload).encode()
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": event_type,
        "X-Hub-Signature-256": sign_payload(body),
    }
    try:
        resp = requests.post(WEBHOOK_URL, data=body, headers=headers, timeout=5)
        return resp.status_code == 200
    except requests.RequestException as e:
        print(f"\033[91m  ✗ Failed to send: {e}\033[0m")
        return False


def _random_files(conflict_file: str | None = None) -> list:
    """Pick random files. If conflict_file given, include it."""
    files = random.sample(FILES, k=random.randint(1, 4))
    if conflict_file and conflict_file not in files:
        files.append(conflict_file)
    return files


# ---------------------------------------------------------------------------
# Event generators
# ---------------------------------------------------------------------------

def gen_push(branch: str = None, conflict_file: str = None) -> tuple:
    """Generate a push event payload."""
    sender = random.choice(CONTRIBUTORS)
    branch = branch or random.choice(BRANCHES)
    files = _random_files(conflict_file)
    num_commits = random.randint(1, 5)
    commits = []
    for _ in range(num_commits):
        commits.append({
            "id": uuid.uuid4().hex,
            "message": random.choice([
                "feat: add new endpoint",
                "fix: resolve null pointer",
                "refactor: clean up utils",
                "docs: update README",
                "test: add unit tests",
                "chore: update dependencies",
            ]),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "author": {"name": sender["login"], "email": f"{sender['login']}@example.com", "username": sender["login"]},
            "added": [f for f in files if random.random() > 0.5] or [files[0]],
            "modified": [f for f in files if random.random() > 0.5],
            "removed": [],
        })
    return "push", {
        "ref": f"refs/heads/{branch}",
        "before": uuid.uuid4().hex,
        "after": uuid.uuid4().hex,
        "repository": {"full_name": "octocat/hello-world", "name": "hello-world", "html_url": "https://github.com/octocat/hello-world"},
        "pusher": {"name": sender["login"], "email": f"{sender['login']}@example.com"},
        "sender": sender,
        "compare": "https://github.com/octocat/hello-world/compare/abc...def",
        "commits": commits,
        "head_commit": commits[-1],
    }


def gen_pull_request() -> tuple:
    """Generate a pull request event payload."""
    global PR_COUNTER
    PR_COUNTER += 1
    sender = random.choice(CONTRIBUTORS)
    action = random.choice(["opened", "closed"])
    merged = action == "closed" and random.random() > 0.4
    source = random.choice([b for b in BRANCHES if b != "main"])
    return "pull_request", {
        "action": action,
        "number": PR_COUNTER,
        "pull_request": {
            "number": PR_COUNTER,
            "title": random.choice(["Add user authentication", "Fix dashboard layout", "Update API docs", "Refactor database layer"]),
            "state": "closed" if action == "closed" else "open",
            "merged": merged,
            "html_url": f"https://github.com/octocat/hello-world/pull/{PR_COUNTER}",
            "user": sender,
            "head": {"ref": source, "sha": uuid.uuid4().hex},
            "base": {"ref": "main", "sha": uuid.uuid4().hex},
        },
        "repository": {"full_name": "octocat/hello-world", "name": "hello-world"},
        "sender": sender,
    }


def gen_branch() -> tuple:
    """Generate a branch create event payload."""
    sender = random.choice(CONTRIBUTORS)
    name = f"feature/{random.choice(['ui', 'api', 'perf', 'i18n'])}-{random.randint(1, 99)}"
    return "create", {
        "ref": name,
        "ref_type": "branch",
        "master_branch": "main",
        "repository": {"full_name": "octocat/hello-world", "name": "hello-world"},
        "sender": sender,
    }


def gen_issue() -> tuple:
    """Generate an issue event payload."""
    sender = random.choice(CONTRIBUTORS)
    num = random.randint(50, 200)
    return "issues", {
        "action": random.choice(["opened", "closed"]),
        "issue": {
            "number": num,
            "title": random.choice(["Login page broken", "Add dark mode", "Improve error messages", "Memory leak in worker"]),
            "html_url": f"https://github.com/octocat/hello-world/issues/{num}",
        },
        "repository": {"full_name": "octocat/hello-world", "name": "hello-world"},
        "sender": sender,
    }


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    """Run the event simulator."""
    global EVENT_COUNTER
    print("\033[96m╔══════════════════════════════════════════════╗\033[0m")
    print("\033[96m║  Git Collaboration Monitor — Event Simulator ║\033[0m")
    print("\033[96m╚══════════════════════════════════════════════╝\033[0m")
    print(f"  Target: {WEBHOOK_URL}")
    print(f"  Secret: {'[set]' if WEBHOOK_SECRET else '[none]'}")
    print()

    generators = [gen_push, gen_push, gen_push, gen_pull_request, gen_branch, gen_issue]

    try:
        while True:
            EVENT_COUNTER += 1

            # Every 10th event: create a conflict scenario
            if EVENT_COUNTER % 10 == 0:
                conflict_file = random.choice(FILES)
                b1, b2 = random.sample([b for b in BRANCHES if b != "main"], 2)
                for branch in [b1, b2]:
                    etype, payload = gen_push(branch=branch, conflict_file=conflict_file)
                    ok = send_event(etype, payload)
                    status = "\033[92m✓\033[0m" if ok else "\033[91m✗\033[0m"
                    print(f"  {status} [{EVENT_COUNTER:04d}] \033[93mCONFLICT\033[0m push → {branch} (file: {conflict_file})")
                    time.sleep(0.5)
            else:
                gen = random.choice(generators)
                etype, payload = gen()
                ok = send_event(etype, payload)
                status = "\033[92m✓\033[0m" if ok else "\033[91m✗\033[0m"
                actor = payload.get("sender", {}).get("login", "?")
                print(f"  {status} [{EVENT_COUNTER:04d}] {etype:16s} by {actor}")

            delay = random.uniform(2, 5)
            time.sleep(delay)
    except KeyboardInterrupt:
        print(f"\n\033[96m  Simulation stopped. Sent {EVENT_COUNTER} events.\033[0m")


if __name__ == "__main__":
    main()
