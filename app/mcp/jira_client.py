from __future__ import annotations

from typing import Any, Optional

from app.mcp.base import MCPToolClient


class JiraMCPClient:
    def __init__(self, client: MCPToolClient):
        self.client = client

    async def get_projects(self) -> Any:
        return await self.client.call_tool("jira_get_all_projects", {})

    async def search_issues(self, jql: str, limit: int = 50) -> Any:
        return await self.client.call_tool(
            "jira_search",
            {
                "jql": jql,
                "limit": limit,
            },
        )

    async def get_issue(self, issue_key: str) -> Any:
        return await self.client.call_tool(
            "jira_get_issue",
            {"issue_key": issue_key},
        )

    async def create_issue(
        self,
        project_key: str,
        summary: str,
        issue_type: str = "Task",
        description: str = "",
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> Any:
        payload: dict[str, Any] = {
            "project_key": project_key,
            "summary": summary,
            "issue_type": issue_type,
        }

        if description:
            payload["description"] = description

        return await self.client.call_tool("jira_create_issue", payload)

    async def update_issue(
        self,
        issue_key: str,
        fields: dict[str, Any],
    ) -> Any:
        return await self.client.call_tool(
            "jira_update_issue",
            {
                "issue_key": issue_key,
                **fields,
            },
        )

    async def transition_issue(
        self,
        issue_key: str,
        transition_id: str,
    ) -> Any:
        return await self.client.call_tool(
            "jira_transition_issue",
            {
                "issue_key": issue_key,
                "transition_id": transition_id,
            },
        )