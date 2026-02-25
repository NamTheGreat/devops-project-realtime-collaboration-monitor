"""
models.py — Pydantic data models for the Git Collaboration Monitor.

Defines the schemas for GitEvent, ConflictAlert, StatsResponse,
and WebhookResponse used throughout the application.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConflictAlert(BaseModel):
    """Schema representing a conflict risk alert between branches."""

    type: str = Field(default="conflict_risk", description="Alert type identifier")
    severity: str = Field(description="Alert severity: 'high' or 'medium'")
    message: str = Field(description="Human-readable conflict description")
    branches: List[str] = Field(description="List of branches involved in the conflict")
    conflicting_files: List[str] = Field(description="File paths that are in conflict")


class GitEvent(BaseModel):
    """Normalized schema for any GitHub webhook event."""

    id: str = Field(description="Unique event identifier (UUID4)")
    timestamp: str = Field(description="ISO 8601 timestamp of the event")
    event_type: str = Field(description="Event type: push, pull_request, branch_create, branch_delete, merge, issues")
    actor: str = Field(description="GitHub username of the actor")
    actor_avatar: str = Field(default="", description="GitHub avatar URL of the actor")
    repository: str = Field(description="Full repository name (owner/repo)")
    branch: str = Field(default="", description="Branch name associated with the event")
    title: str = Field(description="Human-readable one-line summary")
    details: Dict[str, Any] = Field(default_factory=dict, description="Event-specific detail fields")
    files_changed: List[str] = Field(default_factory=list, description="List of changed file paths (for push events)")
    alert: Optional[ConflictAlert] = Field(default=None, description="Conflict alert if detected")


class StatsResponse(BaseModel):
    """Response schema for the /stats endpoint."""

    total_events_today: int = Field(default=0, description="Total webhook events received today")
    active_contributors: int = Field(default=0, description="Unique contributors in the last hour")
    branches_modified: int = Field(default=0, description="Unique branches modified today")
    conflict_alerts: int = Field(default=0, description="Number of conflict alerts today")


class WebhookResponse(BaseModel):
    """Acknowledgment response for the POST /webhook endpoint."""

    status: str = Field(description="Processing status")
    event_type: str = Field(default="", description="The GitHub event type received")
