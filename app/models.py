from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class TaskRow(BaseModel):
    row_number: int
    task_id: Optional[str] = None
    task_name: str
    description: str = ""
    project_key: Optional[str] = None
    issue_type: Optional[str] = None
    jira_issue_key: Optional[str] = None
    sync_status: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None
    raw: dict[str, Any] = Field(default_factory=dict)


class JiraIssueRef(BaseModel):
    key: str
    url: Optional[str] = None


class WorkflowResult(BaseModel):
    ok: bool
    message: str
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    details: list[dict[str, Any]] = Field(default_factory=list)