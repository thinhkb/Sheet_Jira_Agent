from __future__ import annotations

from typing import Any

from app.mcp.jira_client import JiraMCPClient


class RawJiraTools:
    def __init__(self, jira: JiraMCPClient, default_project_key: str):
        self.jira = jira
        self.default_project_key = default_project_key

    async def jira_get_projects(self) -> dict[str, Any]:
        result = await self.jira.get_projects()
        return {"result": result}

    async def jira_search_issues(
        self,
        jql: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        actual_jql = jql or f"project = {self.default_project_key} ORDER BY updated DESC"
        result = await self.jira.search_issues(actual_jql, limit=limit)
        return {"jql": actual_jql, "result": result}

    async def jira_get_issue(self, issue_key: str) -> dict[str, Any]:
        result = await self.jira.get_issue(issue_key)
        return {"issue_key": issue_key, "result": result}

    async def jira_create_issue(
        self,
        summary: str,
        description: str = "",
        issue_type: str = "Task",
        project_key: str | None = None,
    ) -> dict[str, Any]:
        result = await self.jira.create_issue(
            project_key=project_key or self.default_project_key,
            summary=summary,
            issue_type=issue_type,
            description=description,
        )
        return {
            "project_key": project_key or self.default_project_key,
            "summary": summary,
            "result": result,
        }