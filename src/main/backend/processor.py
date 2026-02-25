"""
processor.py — Core event processing logic for the Git Collaboration Monitor.

Parses raw GitHub webhook payloads into normalized GitEvent objects,
detects potential merge conflicts between branches, and generates
human-readable event titles.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


def generate_title(event_type: str, payload: Dict[str, Any]) -> str:
    """
    Generate a human-readable one-line summary for the event.

    Args:
        event_type: The GitHub event type string.
        payload: The raw webhook payload.

    Returns:
        A natural language summary string.
    """
    if event_type == "push":
        pusher = payload.get("pusher", {}).get("name", "someone")
        commits = payload.get("commits", [])
        ref = payload.get("ref", "")
        branch = ref.split("/")[-1] if "/" in ref else ref
        count = len(commits)
        noun = "commit" if count == 1 else "commits"
        return f"{pusher} pushed {count} {noun} to {branch}"

    if event_type == "pull_request":
        pr = payload.get("pull_request", {})
        action = payload.get("action", "updated")
        user = pr.get("user", {}).get("login", "someone")
        number = pr.get("number", "?")
        title = pr.get("title", "")
        merged = pr.get("merged", False)
        if action == "closed" and merged:
            base = pr.get("base", {}).get("ref", "main")
            return f"{user} merged pull request #{number} into {base}"
        return f"{user} {action} PR #{number}: {title}"

    if event_type == "create":
        ref_type = payload.get("ref_type", "branch")
        ref_name = payload.get("ref", "unknown")
        sender = payload.get("sender", {}).get("login", "someone")
        return f"{sender} created {ref_type} {ref_name}"

    if event_type == "delete":
        ref_type = payload.get("ref_type", "branch")
        ref_name = payload.get("ref", "unknown")
        sender = payload.get("sender", {}).get("login", "someone")
        return f"{sender} deleted {ref_type} {ref_name}"

    if event_type == "issues":
        action = payload.get("action", "updated")
        issue = payload.get("issue", {})
        sender = payload.get("sender", {}).get("login", "someone")
        number = issue.get("number", "?")
        title = issue.get("title", "")
        return f"{sender} {action} issue #{number}: {title}"

    sender = payload.get("sender", {}).get("login", "someone")
    return f"{sender} triggered {event_type} event"


def _extract_files_changed(payload: Dict[str, Any]) -> List[str]:
    """
    Extract unique file paths changed in a push event.

    Args:
        payload: Raw push event payload.

    Returns:
        Sorted list of unique file paths.
    """
    files: set = set()
    for commit in payload.get("commits", []):
        files.update(commit.get("added", []))
        files.update(commit.get("modified", []))
        files.update(commit.get("removed", []))
    return sorted(files)


def parse_event(event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a raw GitHub webhook payload into a normalized event dictionary.

    Args:
        event_type: The GitHub event type (e.g. 'push', 'pull_request').
        payload: The raw JSON payload from GitHub.

    Returns:
        A normalized event dictionary matching the GitEvent schema.
    """
    now = datetime.now(timezone.utc).isoformat()
    sender = payload.get("sender", {})
    repo = payload.get("repository", {})

    event: Dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "timestamp": now,
        "event_type": event_type,
        "actor": sender.get("login", "unknown"),
        "actor_avatar": sender.get("avatar_url", ""),
        "repository": repo.get("full_name", "unknown/unknown"),
        "branch": "",
        "title": generate_title(event_type, payload),
        "details": {},
        "files_changed": [],
        "alert": None,
    }

    if event_type == "push":
        ref = payload.get("ref", "")
        event["branch"] = ref.split("/")[-1] if "/" in ref else ref
        event["files_changed"] = _extract_files_changed(payload)
        event["details"] = {
            "commits": len(payload.get("commits", [])),
            "before": payload.get("before", ""),
            "after": payload.get("after", ""),
            "compare_url": payload.get("compare", ""),
        }

    elif event_type == "pull_request":
        pr = payload.get("pull_request", {})
        action = payload.get("action", "")
        merged = pr.get("merged", False)
        event["event_type"] = "merge" if action == "closed" and merged else "pull_request"
        event["branch"] = pr.get("head", {}).get("ref", "")
        event["details"] = {
            "action": action,
            "pr_number": pr.get("number"),
            "pr_title": pr.get("title", ""),
            "source_branch": pr.get("head", {}).get("ref", ""),
            "target_branch": pr.get("base", {}).get("ref", ""),
            "merged": merged,
            "html_url": pr.get("html_url", ""),
        }

    elif event_type == "create":
        event["event_type"] = "branch_create"
        event["branch"] = payload.get("ref", "")
        event["details"] = {
            "ref_type": payload.get("ref_type", "branch"),
        }

    elif event_type == "delete":
        event["event_type"] = "branch_delete"
        event["branch"] = payload.get("ref", "")
        event["details"] = {
            "ref_type": payload.get("ref_type", "branch"),
        }

    elif event_type == "issues":
        issue = payload.get("issue", {})
        event["details"] = {
            "action": payload.get("action", ""),
            "issue_number": issue.get("number"),
            "issue_title": issue.get("title", ""),
            "html_url": issue.get("html_url", ""),
        }

    return event


def detect_conflicts(
    new_event: Dict[str, Any],
    recent_events: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Detect potential merge conflicts between the new event and recent push events.

    Checks if two different branches have modified the same file within
    a 10-minute window, returning a conflict alert if found.

    Args:
        new_event: The newly parsed event dictionary.
        recent_events: Last N push events from Redis.

    Returns:
        A conflict alert dict, or None if no conflicts detected.
    """
    if new_event.get("event_type") != "push":
        return None

    new_files = set(new_event.get("files_changed", []))
    if not new_files:
        return None

    new_branch = new_event.get("branch", "")
    try:
        new_ts = datetime.fromisoformat(new_event["timestamp"])
    except (ValueError, KeyError):
        new_ts = datetime.now(timezone.utc)

    window = timedelta(minutes=10)
    conflicting_files: List[str] = []
    conflict_branches: set = set()

    for ev in recent_events:
        if ev.get("event_type") != "push":
            continue
        ev_branch = ev.get("branch", "")
        if ev_branch == new_branch or not ev_branch:
            continue

        try:
            ev_ts = datetime.fromisoformat(ev["timestamp"])
        except (ValueError, KeyError):
            continue

        if (new_ts - ev_ts) > window:
            continue

        overlap = new_files.intersection(set(ev.get("files_changed", [])))
        if overlap:
            conflicting_files.extend(overlap)
            conflict_branches.add(ev_branch)

    if not conflicting_files:
        return None

    unique_files = sorted(set(conflicting_files))
    branches_list = sorted(conflict_branches)
    severity = "high" if len(unique_files) >= 3 else "medium"

    return {
        "type": "conflict_risk",
        "severity": severity,
        "message": (
            f"Branch '{new_branch}' and '{branches_list[0]}' "
            f"both modified '{unique_files[0]}'"
            + (f" and {len(unique_files) - 1} more file(s)" if len(unique_files) > 1 else "")
        ),
        "branches": [new_branch] + branches_list,
        "conflicting_files": unique_files,
    }
