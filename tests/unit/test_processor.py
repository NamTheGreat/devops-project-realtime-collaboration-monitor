"""
test_processor.py — Unit tests for the event processor module.

Tests event parsing, conflict detection, and title generation for
all supported GitHub event types.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

import pytest

# Ensure the backend module is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "main", "backend"))

from processor import detect_conflicts, generate_title, parse_event

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "test-data")


def _load_sample(filename: str) -> dict:
    with open(os.path.join(DATA_DIR, filename), "r") as f:
        return json.load(f)


# ---- parse_event tests ----

class TestParseEvent:
    """Tests for the parse_event function."""

    def test_parse_push_event(self):
        """Push events should extract commits, branch, files changed."""
        payload = _load_sample("sample_push_event.json")
        event = parse_event("push", payload)
        assert event["event_type"] == "push"
        assert event["actor"] == "alice"
        assert event["branch"] == "feature/auth"
        assert event["repository"] == "octocat/hello-world"
        assert "src/auth.py" in event["files_changed"]
        assert "src/main.py" in event["files_changed"]
        assert event["details"]["commits"] == 3
        assert event["id"]  # UUID should be present
        assert event["timestamp"]  # ISO timestamp

    def test_parse_pr_event(self):
        """Pull request opened events should capture PR details."""
        payload = _load_sample("sample_pr_event.json")
        event = parse_event("pull_request", payload)
        assert event["event_type"] == "pull_request"
        assert event["actor"] == "bob"
        assert event["details"]["pr_number"] == 42
        assert event["details"]["action"] == "opened"
        assert event["details"]["source_branch"] == "feature/auth"
        assert event["details"]["target_branch"] == "main"

    def test_parse_pr_merged_event(self):
        """Merged PRs should be classified as 'merge' event type."""
        payload = _load_sample("sample_pr_event.json")
        payload["action"] = "closed"
        payload["pull_request"]["merged"] = True
        event = parse_event("pull_request", payload)
        assert event["event_type"] == "merge"
        assert event["details"]["merged"] is True

    def test_parse_branch_create_event(self):
        """Branch creation events should extract branch name and ref type."""
        payload = _load_sample("sample_branch_event.json")
        event = parse_event("create", payload)
        assert event["event_type"] == "branch_create"
        assert event["branch"] == "hotfix/payment-bug"
        assert event["actor"] == "carol"

    def test_parse_issues_event(self):
        """Issue events should extract issue number and title."""
        payload = {
            "action": "opened",
            "issue": {
                "number": 10,
                "title": "Fix login bug",
                "html_url": "https://github.com/octocat/hello-world/issues/10",
            },
            "repository": {"full_name": "octocat/hello-world"},
            "sender": {"login": "dave", "avatar_url": "https://avatars.githubusercontent.com/u/4?v=4"},
        }
        event = parse_event("issues", payload)
        assert event["event_type"] == "issues"
        assert event["details"]["issue_number"] == 10


# ---- detect_conflicts tests ----

class TestDetectConflicts:
    """Tests for the detect_conflicts function."""

    def _make_push(self, branch: str, files: list, minutes_ago: int = 0) -> dict:
        ts = (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).isoformat()
        return {
            "event_type": "push",
            "branch": branch,
            "files_changed": files,
            "timestamp": ts,
            "actor": "test-user",
        }

    def test_detect_conflict_found(self):
        """Two branches modifying the same file within 10 minutes → conflict."""
        new = self._make_push("feature/x", ["src/auth.py", "src/utils.py"])
        recent = [self._make_push("feature/y", ["src/auth.py", "README.md"], minutes_ago=3)]
        result = detect_conflicts(new, recent)
        assert result is not None
        assert result["type"] == "conflict_risk"
        assert "src/auth.py" in result["conflicting_files"]
        assert "feature/x" in result["branches"]
        assert "feature/y" in result["branches"]

    def test_detect_conflict_not_found(self):
        """Different files modified → no conflict."""
        new = self._make_push("feature/x", ["src/auth.py"])
        recent = [self._make_push("feature/y", ["src/database.py"], minutes_ago=2)]
        result = detect_conflicts(new, recent)
        assert result is None

    def test_detect_conflict_too_old(self):
        """Same file but push was 15 minutes ago → outside window, no conflict."""
        new = self._make_push("feature/x", ["src/auth.py"])
        recent = [self._make_push("feature/y", ["src/auth.py"], minutes_ago=15)]
        result = detect_conflicts(new, recent)
        assert result is None

    def test_detect_conflict_same_branch(self):
        """Same branch modifying same file → not a conflict."""
        new = self._make_push("feature/x", ["src/auth.py"])
        recent = [self._make_push("feature/x", ["src/auth.py"], minutes_ago=1)]
        result = detect_conflicts(new, recent)
        assert result is None

    def test_detect_conflict_non_push(self):
        """Non-push events should be ignored."""
        new = {"event_type": "pull_request", "branch": "feature/x", "files_changed": [], "timestamp": datetime.now(timezone.utc).isoformat()}
        result = detect_conflicts(new, [])
        assert result is None


# ---- generate_title tests ----

class TestGenerateTitle:
    """Tests for the generate_title function."""

    def test_generate_title_push(self):
        """Push title should include commit count and branch."""
        payload = _load_sample("sample_push_event.json")
        title = generate_title("push", payload)
        assert "pushed" in title
        assert "3" in title
        assert "feature/auth" in title

    def test_generate_title_pr_opened(self):
        """PR opened title should include PR number and title."""
        payload = _load_sample("sample_pr_event.json")
        title = generate_title("pull_request", payload)
        assert "bob" in title
        assert "#42" in title

    def test_generate_title_pr_merged(self):
        """PR merged title should include 'merged'."""
        payload = _load_sample("sample_pr_event.json")
        payload["action"] = "closed"
        payload["pull_request"]["merged"] = True
        title = generate_title("pull_request", payload)
        assert "merged" in title

    def test_generate_title_branch_create(self):
        """Branch creation title should include 'created'."""
        payload = _load_sample("sample_branch_event.json")
        title = generate_title("create", payload)
        assert "created" in title
        assert "hotfix/payment-bug" in title
