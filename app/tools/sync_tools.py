from __future__ import annotations

from typing import Any

from app.agent.orchestrator import AgentOrchestrator


class SyncTools:
    def __init__(self, orchestrator: AgentOrchestrator):
        self.orchestrator = orchestrator

    async def sync_sheet_to_jira(self) -> dict[str, Any]:
        result = await self.orchestrator.run_sync_sheet_to_jira()
        return result.model_dump()

    async def sync_jira_to_sheet(self) -> dict[str, Any]:
        result = await self.orchestrator.run_sync_jira_to_sheet()
        return result.model_dump()

    async def get_sync_status(self) -> dict[str, Any]:
        s = self.orchestrator.settings
        return {
            "spreadsheet_id": s.default_spreadsheet_id,
            "tasks_sheet": s.default_tasks_sheet,
            "jira_project_key": s.default_jira_project_key,
            "jira_issue_type": s.default_jira_issue_type,
        }